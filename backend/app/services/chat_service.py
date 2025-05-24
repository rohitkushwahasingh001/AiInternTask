# backend/app/services/chat_service.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict, Tuple
import json
import logging

from app.services.vector_db_service import VectorDBService
from app.models.responses import Citation

logger = logging.getLogger(__name__)

class ChatService:
    """
    Handles interactions with the Google Gemini LLM for query answering.
    """
    # Define a maximum character length for the combined text sent for theme identification.
    MAX_THEME_TEXT_LENGTH = 10000

    def __init__(self, gemini_api_key: str):
       
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_api_key, temperature=0)
        logger.info("ChatService initialized with Google Gemini 1.5 Flash LLM.")

    async def query_documents(self, query: str, vector_db_service: VectorDBService) -> Dict:
        """
        Uses the LLM to answer a user query based on provided relevant document chunks.
        The response will include citations to the source documents.
        The response will be concise.
        """
        logger.info(f"Querying documents for: {query}")

        retrieved_chunks = vector_db_service.query_documents(query, n_results=5) 
        
        if not retrieved_chunks:
            logger.info("No relevant documents found for query.")
            return {
                "synthesized_response": "No relevant documents found for your query. Please upload documents first or try a different query.",
                "tabular_citations": []
            }

        context_string = "\n\n".join([
            f"Document ID: {doc['metadata']['document_id']}, Filename: {doc['metadata']['filename']}, "
            f"Page: {doc['metadata']['page']}, Paragraph: {doc['metadata']['paragraph_global']}\n"
            f"Content: {doc['content']}"
            for doc in retrieved_chunks
        ])

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant that answers user queries based on the provided documents. "
                           "Be concise and directly answer the question. Do not add conversational filler. "
                           "Cite the document ID, filename, page, and global paragraph number for each piece of information you use. "
                           "Format citations as (DOC_ID: [DOC_ID], File: [Filename], Page: [Page_Num], Para: [Para: [Para_Num]). "
                           "If the information is not in the provided context, state that you cannot answer based on the given documents."),
                ("human", "Given the following context:\n\n{context}\n\nAnswer the following question: {query}")
            ]
        )

        chain = (
            {"context": RunnablePassthrough(), "query": RunnablePassthrough()}
            | prompt_template
            | self.llm
            | StrOutputParser()
        )
        
      
        synthesized_response = await chain.ainvoke({"context": context_string, "query": query})
        logger.info(f"LLM generated response for query: {query}")

        tabular_citations = []
        unique_citations = set() 
        for chunk in retrieved_chunks:
            metadata = chunk['metadata']
            citation_identifier = (
                metadata.get("document_id"),
                metadata.get("filename"),
                metadata.get("page"),
                metadata.get("paragraph_global")
            )
            if citation_identifier not in unique_citations:
                tabular_citations.append(Citation(
                    document_id=metadata.get("document_id"),
                    filename=metadata.get("filename"),
                    page=metadata.get("page"),
                    paragraph=metadata.get("paragraph_global"),
                    text_content=chunk['content']
                ))
                unique_citations.add(citation_identifier)
        
        return {
            "synthesized_response": synthesized_response,
            "tabular_citations": tabular_citations
        }

    async def identify_themes(self, chunks_for_themes: List[Dict]) -> Tuple[List[Dict], Dict[str, List[str]]]:
        """
        Analyzes a collection of document chunks (can be all or just relevant ones)
        to identify common themes and map these themes to relevant document IDs.
        chunks_for_themes: List of dictionaries, where each dict has 'document_id' and 'text_content' keys.
        """
        logger.info("Starting theme identification process within ChatService.")
        if not chunks_for_themes:
            logger.warning("No chunks provided for theme identification.")
            return [], {}

        combined_text_for_themes = ""
        unique_doc_ids_in_chunks = set()
        truncated = False

        for i, chunk in enumerate(chunks_for_themes):
            doc_id = chunk.get('document_id', 'UNKNOWN_DOC')
            content = chunk.get('text_content', '')
            
            chunk_content = f"Document ID: {doc_id}\nContent: {content}\n\n"
            
            if len(combined_text_for_themes) + len(chunk_content) > self.MAX_THEME_TEXT_LENGTH:
                truncated = True
                break

            combined_text_for_themes += chunk_content
            unique_doc_ids_in_chunks.add(doc_id)
            
        if truncated:
            logger.warning(f"Combined text for theme identification truncated to {self.MAX_THEME_TEXT_LENGTH} characters to fit LLM context.")


        theme_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert at identifying common themes across multiple document snippets. "
                           "Your task is to analyze the provided text and identify distinct, coherent themes. "
                           "For each theme, list the document IDs that are relevant to that theme. "
                           "Return the output as a JSON object with two keys: 'themes' (a list of theme names) "
                           "and 'theme_citations' (a dictionary mapping theme names to a list of relevant document IDs). "
                           "Ensure document IDs are accurately extracted from the provided text. "
                           "Example: {{'themes': ['Regulatory Compliance', 'Financial Penalties'], 'theme_citations': {{'Regulatory Compliance': ['DOC001', 'DOC002'], 'Financial Penalties': ['DOC001']}}}}"),
                ("human", "Analyze the following information from various documents and identify common themes, linking them to document IDs. "
                           "Here is the combined information:\n\n{combined_info}\n\n"
                           "Please provide the output in the specified JSON format. Only output the JSON.")
            ]
        )

        chain = (
            theme_prompt
            | self.llm
            | StrOutputParser()
        )

        raw_themes_response = await chain.ainvoke({"combined_info": combined_text_for_themes})

        themes = []
        theme_citations = {}

        try:
            parsed_response = json.loads(raw_themes_response)
            themes = parsed_response.get("themes", [])
            for theme, doc_ids in parsed_response.get("theme_citations", {}).items():
                theme_citations[theme] = list(set(doc_id for doc_id in doc_ids if doc_id in unique_doc_ids_in_chunks))
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing theme identification response as JSON: {e}. Raw response: {raw_themes_response}", exc_info=True)
            themes = ["General Document Analysis"]
            theme_citations = {"General Document Analysis": list(unique_doc_ids_in_chunks)}
        except Exception as e:
            logger.error(f"An unexpected error occurred during theme identification: {e}. Raw response: {raw_themes_response}", exc_info=True)
            themes = ["General Document Analysis"]
            theme_citations = {"General Document Analysis": list(unique_doc_ids_in_chunks)}

        return themes, theme_citations
