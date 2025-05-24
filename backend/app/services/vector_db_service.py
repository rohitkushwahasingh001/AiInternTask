# backend/app/services/vector_db_service.py

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SentenceTransformerEmbeddingFunction(embedding_functions.SentenceTransformerEmbeddingFunction):
    """
    Custom SentenceTransformerEmbeddingFunction to use a specific model.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", **kwargs):
        super().__init__(model_name=model_name, **kwargs)

class VectorDBService:
    """
    Manages interactions with the ChromaDB vector database.
    """
    def __init__(self, db_path: str):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_function = SentenceTransformerEmbeddingFunction()
        self.collection_name = "document_chunks"
        self._get_or_create_collection()
        logger.info(f"ChromaDB initialized. Collection '{self.collection_name}' ready.")

    def _get_or_create_collection(self):
        """Ensures the collection exists."""
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function # Ensure embedding function is set
            )
            logger.info(f"Existing ChromaDB collection '{self.collection_name}' loaded.")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"New ChromaDB collection '{self.collection_name}' created.")

    def add_documents(self, chunks: List[Dict]):
        """
        Adds processed document chunks to the ChromaDB collection.
        Each chunk is a dictionary with 'content' and 'metadata'.
        """
        if not chunks:
            logger.warning("No chunks provided to add to ChromaDB.")
            return

        documents = [chunk['content'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        ids = [f"{m['document_id']}_p{m['paragraph_global']}" for m in metadatas]

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(chunks)} chunks to ChromaDB.")
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}", exc_info=True)
            raise

    def query_documents(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """
        Queries the ChromaDB for relevant document chunks based on a query text.
        Returns a list of dictionaries, each containing 'content' and 'metadata'.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=['documents', 'metadatas']
            )
            
            retrieved_chunks = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    retrieved_chunks.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i]
                    })
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query.")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error querying documents from ChromaDB: {e}", exc_info=True)
            return []

    def list_documents(self) -> List[Dict]:
        """
        Retrieves metadata for all unique documents stored in the ChromaDB collection.
        Returns a list of dictionaries, each with 'document_id' and 'filename'.
        """
        try:
         
            # A large limit is used to ensure all documents are fetched.
        
            all_chunks_data = self.collection.get(
                limit=100000, # Fetch up to 100,000 chunks
                include=['metadatas']
            )
            all_chunks_metadata = all_chunks_data['metadatas']

            unique_docs = {}
            for metadata in all_chunks_metadata:
                doc_id = metadata.get('document_id')
                filename = metadata.get('filename')
                if doc_id and filename and doc_id not in unique_docs:
                    unique_docs[doc_id] = {
                        "document_id": doc_id,
                        "filename": filename,
                        # "uploaded_at": metadata.get('uploaded_at') # Add if you store this
                    }
            
            documents_list = list(unique_docs.values())
            logger.info(f"Listed {len(documents_list)} unique documents from ChromaDB.")
            return documents_list
        except Exception as e:
            logger.error(f"Error listing documents from ChromaDB: {e}", exc_info=True)
            return []

    def delete_all_documents(self):
        """
        Deletes all documents from the ChromaDB collection.
        This effectively clears the knowledge base.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            self._get_or_create_collection() # Recreate empty collection
            logger.info(f"ChromaDB collection '{self.collection_name}' cleared.")
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}", exc_info=True)
            raise
