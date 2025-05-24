# backend/app/services/theme_identifier.py

from typing import List, Dict
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

class ThemeIdentifierService:
    """Service to identify themes from a collection of documents."""

    def __init__(self, vector_store: Chroma, llm: ChatGoogleGenerativeAI):
        self.vector_store = vector_store
        self.llm = llm

    async def identify_themes(self) -> List[Dict]:
        """
        Identifies common themes from all documents in the vector store.
        The themes are identified using an LLM based on summarized document chunks.
        """
        logger.info("Starting theme identification process.")

        try:
            # Fetch all documents (chunks) from the vector store
       
            all_documents = self.vector_store.get(where={})['documents']

            if not all_documents:
                logger.warning("No documents found in the vector store for theme identification.")
                return []

            # Create Document objects from the fetched content for summarization chain
            langchain_docs = [Document(page_content=doc) for doc in all_documents]

            # Define a concise summarization prompt for each chunk
            # This helps to get a brief overview of each chunk
            map_prompt_template = """The following is a part of a larger document:
            "{text}"
            Provide a concise summary of this part, focusing on the main topics and key information.
            Concise summary:"""
            map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])

            # Define the final prompt to identify overarching themes from the summaries
            combine_prompt_template = """Given the following summaries of various documents, identify and list 3-5 distinct common themes. For each theme, provide a concise description and list the relevant document IDs.
            Ensure themes are distinct and meaningful.
            Summaries:
            {text}

            Example Output Format:
            - Theme 1: [Concise description of Theme 1] (Documents: DOC_ID1, DOC_ID2)
            - Theme 2: [Concise description of Theme 2] (Documents: DOC_ID3, DOC_ID4)

            Identified Themes:"""
            combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])

            # Use LangChain's summarize chain with 'map_reduce' strategy
            # 'map_reduce' first summarizes individual chunks (map) and then combines
            # these summaries to identify overarching themes (reduce/combine).
            summarize_chain = load_summarize_chain(
                self.llm,
                chain_type="map_reduce",
                map_prompt=map_prompt,
                combine_prompt=combine_prompt,
                verbose=True # Set to False for production to reduce logging
            )

            # Run the summarization chain to identify themes
            identified_themes_text = await summarize_chain.arun(langchain_docs)

            # The LLM output is a string; we need to parse it into a structured list.
            # This parsing is an example and might need adjustment based on LLM's exact output format.
            # A more robust parsing might involve regex or a more structured LLM output (e.g., JSON).
            themes_list = self._parse_themes_output(identified_themes_text)

            logger.info("Theme identification completed successfully.")
            return themes_list

        except Exception as e:
            logger.error(f"Error during theme identification: {e}", exc_info=True)
            raise

    def _parse_themes_output(self, text: str) -> List[Dict]:
        """
        Parses the raw text output from the LLM into a structured list of themes.
        Assumes themes are listed with a hyphen or similar indicator.
        Example: "- Theme 1: Description (Documents: DOC001, DOC002)"
        """
        themes = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- Theme'):
                try:
                    # Expected format: "- Theme N: [Description] (Documents: DOC_ID1, DOC_ID2)"
                    parts = line.split(': ', 1) # Split on first colon to get theme name and rest
                    if len(parts) < 2:
                        continue
                    
                    theme_name_part = parts[0].replace('- ', '').strip() # e.g., "Theme 1"
                    description_citation_part = parts[1].strip()

                    # Extract description and citations
                    citation_match = description_citation_part.rfind('(Documents:')
                    description = ""
                    doc_ids = []

                    if citation_match != -1:
                        description = description_citation_part[:citation_match].strip()
                        citation_str = description_citation_part[citation_match:].strip()
                        # Extract IDs from "(Documents: DOC001, DOC002)"
                        doc_id_match = citation_str.replace('(Documents:', '').replace(')', '').strip()
                        doc_ids = [d.strip() for d in doc_id_match.split(',') if d.strip()]
                    else:
                        description = description_citation_part # No citations found, whole thing is description

                    themes.append({
                        "theme_name": theme_name_part,
                        "description": description,
                        "documents": doc_ids
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse theme line: '{line}' - Error: {e}")
        return themes

