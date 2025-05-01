import os
from typing import List, Tuple, Dict
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from pypdf import PdfReader
from datetime import datetime

class RAGEngine:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.documents: List[str] = []
        self.embeddings = None
        self.processed_files: Dict[str, dict] = {}  # Track processed files and their metadata

    def _get_embedding(self, text: str) -> np.ndarray:
        # Tokenize and get model output
        inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use mean pooling to get text embedding
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sentence_embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        return sentence_embedding.numpy()

    def add_pdf(self, pdf_path: str, chunk_size: int = 200) -> None:
        """Add a PDF document to the knowledge base"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            
            # Simple text chunking by words
            words = text.split()
            chunks = [" ".join(words[i:i + chunk_size]) 
                     for i in range(0, len(words), chunk_size)]
            
            # Store file metadata
            filename = os.path.basename(pdf_path)
            self.processed_files[filename] = {
                'chunks': len(chunks),
                'pages': len(reader.pages),
                'processed_at': datetime.now().isoformat(),
                'start_index': len(self.documents)
            }
            
            self.add_texts(chunks)
            return {
                'filename': filename,
                'chunks': len(chunks),
                'pages': len(reader.pages)
            }
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def get_processed_files(self) -> List[Dict]:
        """Get list of processed files and their metadata"""
        return [
            {
                'filename': filename,
                **metadata
            }
            for filename, metadata in self.processed_files.items()
        ]

    def add_texts(self, texts: List[str]) -> None:
        """Add text documents to the knowledge base"""
        if not texts:
            return

        # Create embeddings for new documents
        new_embeddings = []
        for text in texts:
            embedding = self._get_embedding(text)
            new_embeddings.append(embedding)
        
        new_embeddings = np.vstack(new_embeddings)
        
        # Update embeddings
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        self.documents.extend(texts)

    def query(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Query the knowledge base and return relevant documents"""
        if not self.documents or self.embeddings is None:
            return []

        # Create query embedding
        query_embedding = self._get_embedding(query)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top k documents
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return relevant documents and their similarities
        results = []
        for idx in top_k_indices:
            # Find which file this chunk belongs to
            file_info = None
            for filename, metadata in self.processed_files.items():
                if metadata['start_index'] <= idx < metadata['start_index'] + metadata['chunks']:
                    file_info = filename
                    break
            
            results.append({
                'content': self.documents[idx],
                'similarity': float(similarities[idx]),
                'file': file_info
            })
        
        return results

    def get_context_for_query(self, query: str, k: int = 3) -> str:
        """Get relevant context for a query"""
        results = self.query(query, k)
        if not results:
            return ""
        
        # Combine relevant documents into context
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"[From {result['file']}] Document {i+1}:\n{result['content']}")
        
        return "\n\n".join(context_parts)
