import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

class ChromaDocumentManager:
    def __init__(self, collection_name: str = "pdf_documents"):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.Client()
        self.collection_name = collection_name
        
        # Try to get existing collection first, create if it doesn't exist
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✅ Connected to existing collection: {self.collection_name}")
        except Exception:
            try:
                self.collection = self.client.create_collection(name=self.collection_name)
                print(f"✅ Created new collection: {self.collection_name}")
            except chromadb.errors.InternalError as e:
                if "already exists" in str(e):
                    # Collection exists but get_collection failed, try to get it again
                    self.collection = self.client.get_collection(name=self.collection_name)
                    print(f"✅ Retrieved existing collection: {self.collection_name}")
                else:
                    raise e
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def reset_collection(self):
        """Delete and recreate the collection (useful for debugging)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"🗑️ Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"Could not delete collection: {e}")
        
        try:
            self.collection = self.client.create_collection(name=self.collection_name)
            print(f"✅ Created fresh collection: {self.collection_name}")
        except Exception as e:
            print(f"Error creating fresh collection: {e}")
            raise

    def store_document(self, text: str, document_id: str):
        """Store document text in ChromaDB after splitting into chunks."""
        if not text or not text.strip():
            print(f"⚠️ Empty text provided for document {document_id}")
            return
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        print(f"📄 Splitting document {document_id} into {len(chunks)} chunks")
        
        # Remove existing chunks for this document first (if any)
        self.remove_document(document_id)
        
        # Store chunks in ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():  # Only store non-empty chunks
                documents.append(chunk)
                metadatas.append({
                    "source": document_id, 
                    "chunk": i,
                    "chunk_length": len(chunk)
                })
                ids.append(f"{document_id}_chunk_{i}")
        
        if documents:
            try:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Stored {len(documents)} chunks for document {document_id}")
            except Exception as e:
                print(f"❌ Error storing document {document_id}: {e}")
                raise
        else:
            print(f"⚠️ No valid chunks found for document {document_id}")

    def remove_document(self, document_id: str):
        """Remove all chunks for a specific document."""
        try:
            # Get all IDs that start with this document_id
            results = self.collection.get()
            if results and results["ids"]:
                ids_to_delete = [id for id in results["ids"] if id.startswith(f"{document_id}_chunk_")]
                if ids_to_delete:
                    self.collection.delete(ids=ids_to_delete)
                    print(f"🗑️ Removed {len(ids_to_delete)} existing chunks for {document_id}")
        except Exception as e:
            print(f"Warning: Could not remove existing chunks for {document_id}: {e}")

    def query_document(self, query: str, n_results: int = 3, document_id: str = None):
        """Query the document collection and return relevant chunks."""
        try:
            # Build where clause if specific document requested
            where_clause = None
            if document_id:
                where_clause = {"source": {"$eq": document_id}}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            if not results["documents"] or not results["documents"][0]:
                print(f"🔍 No results found for query: '{query[:50]}...'")
                return None
            
            # Join the relevant chunks into a single context
            chunks = results["documents"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            
            print(f"🔍 Found {len(chunks)} relevant chunks for query")
            
            # Add metadata info to help with debugging
            context_parts = []
            for i, (chunk, metadata) in enumerate(zip(chunks, metadatas)):
                source = metadata.get("source", "unknown") if metadata else "unknown"
                chunk_num = metadata.get("chunk", i) if metadata else i
                context_parts.append(f"[Source: {source}, Chunk: {chunk_num}]\n{chunk}")
            
            context = "\n\n".join(context_parts)
            return context
            
        except Exception as e:
            print(f"❌ Error querying documents: {e}")
            return None

    def list_documents(self):
        """List all stored documents."""
        try:
            results = self.collection.get()
            if results and results["metadatas"]:
                sources = set()
                for metadata in results["metadatas"]:
                    if "source" in metadata:
                        sources.add(metadata["source"])
                return list(sources)
            return []
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return []

    def get_collection_stats(self):
        """Get statistics about the collection."""
        try:
            results = self.collection.get()
            if results:
                total_chunks = len(results["ids"]) if results["ids"] else 0
                sources = set()
                if results["metadatas"]:
                    for metadata in results["metadatas"]:
                        if "source" in metadata:
                            sources.add(metadata["source"])
                
                return {
                    "total_chunks": total_chunks,
                    "unique_documents": len(sources),
                    "document_list": list(sources)
                }
            return {"total_chunks": 0, "unique_documents": 0, "document_list": []}
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {"error": str(e)}

    def search_by_patient_name(self, patient_name: str, n_results: int = 5):
        """Specialized search for patient information."""
        query = f"patient name {patient_name} demographics information"
        return self.query_document(query, n_results=n_results)

# Example usage and testing
if __name__ == "__main__":
    # Test the ChromaDB manager
    db_manager = ChromaDocumentManager()
    
    # Print collection stats
    stats = db_manager.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    # Test storing a simple document
    test_text = """
    DISCHARGE SUMMARY
    Patient Name: John Smith
    Date of Birth: 01/15/1980
    Admission Date: 03/15/2024
    Discharge Date: 03/20/2024
    Primary Diagnosis: Acute appendicitis
    """
    
    db_manager.store_document(test_text, "test_document_1")
    
    # Test querying
    result = db_manager.query_document("patient name")
    if result:
        print(f"Query result: {result[:200]}...")
    
    # List all documents
    docs = db_manager.list_documents()
    print(f"Stored documents: {docs}")