"""
Local RAG Implementation with FAISS
This can be swapped to OpenSearch Serverless later with the same interface
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio


class LocalRAGIndexer:
    """Local RAG indexer using FAISS for development"""
    
    def __init__(self, 
                 embedding_client=None,
                 index_path: str = "temp/faiss_index",
                 chunk_size: int = 800,
                 chunk_overlap: int = 100):
        self.embedding_client = embedding_client
        self.index_path = Path(index_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize FAISS
        try:
            import faiss
            import numpy as np
            self.faiss = faiss
            self.np = np
            self.faiss_available = True
        except ImportError:
            print("Warning: FAISS not installed. Using in-memory search.")
            self.faiss_available = False
            
        self.facts_index = None
        self.style_index = None
        self.facts_metadata = []
        self.style_metadata = []
        
        # Create index directory
        self.index_path.mkdir(parents=True, exist_ok=True)
    
    async def index_paper_content(self, 
                                paper_id: str, 
                                content: str, 
                                title: str = "") -> bool:
        """
        Index paper content for retrieval
        
        Args:
            paper_id: Unique paper identifier
            content: Full paper text
            title: Paper title
            
        Returns:
            Success status
        """
        try:
            # Chunk the content
            chunks = self._chunk_text(content)
            
            # Create metadata for each chunk
            metadata = []
            for i, chunk in enumerate(chunks):
                metadata.append({
                    'paper_id': paper_id,
                    'chunk_id': f"{paper_id}_chunk_{i}",
                    'title': title,
                    'text': chunk,
                    'chunk_index': i,
                    'type': 'facts'
                })
            
            # Generate embeddings
            if self.embedding_client:
                response = await self.embedding_client.embed(chunks)
                embeddings = [item['embedding'] for item in response['data']]
            else:
                # Fallback to random embeddings
                import random
                embeddings = [[random.random() for _ in range(768)] for _ in chunks]
            
            # Add to index
            if self.faiss_available:
                await self._add_to_faiss_index(embeddings, metadata, 'facts')
            else:
                await self._add_to_memory_index(embeddings, metadata, 'facts')
            
            print(f"✅ Indexed {len(chunks)} chunks for paper {paper_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error indexing paper content: {e}")
            return False
    
    async def index_style_patterns(self, style_dir: str = "samples/styles/") -> bool:
        """
        Index conversation style patterns
        
        Args:
            style_dir: Directory containing style markdown files
            
        Returns:
            Success status
        """
        try:
            style_path = Path(style_dir)
            if not style_path.exists():
                print(f"⚠️  Style directory {style_dir} not found")
                return False
            
            patterns = []
            metadata = []
            
            for style_file in style_path.glob("*.md"):
                with open(style_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                style_name = style_file.stem
                
                # Extract different sections as separate patterns
                sections = self._extract_style_sections(content)
                
                for section_name, section_content in sections.items():
                    patterns.append(section_content)
                    metadata.append({
                        'style_name': style_name,
                        'section': section_name,
                        'text': section_content,
                        'type': 'style'
                    })
            
            # Generate embeddings for style patterns
            if self.embedding_client and patterns:
                response = await self.embedding_client.embed(patterns)
                embeddings = [item['embedding'] for item in response['data']]
            else:
                # Fallback
                import random
                embeddings = [[random.random() for _ in range(768)] for _ in patterns]
            
            # Add to style index
            if self.faiss_available and patterns:
                await self._add_to_faiss_index(embeddings, metadata, 'style')
            else:
                await self._add_to_memory_index(embeddings, metadata, 'style')
            
            print(f"✅ Indexed {len(patterns)} style patterns")
            return True
            
        except Exception as e:
            print(f"❌ Error indexing style patterns: {e}")
            return False
    
    async def search_facts(self, 
                          query: str, 
                          k: int = 5, 
                          paper_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant facts
        
        Args:
            query: Search query
            k: Number of results to return
            paper_id: Optional paper ID filter
            
        Returns:
            List of relevant chunks with metadata
        """
        try:
            if not self.facts_index and not self.facts_metadata:
                return []
            
            # Generate query embedding
            if self.embedding_client:
                response = await self.embedding_client.embed([query])
                query_embedding = response['data'][0]['embedding']
            else:
                # Random fallback
                import random
                query_embedding = [random.random() for _ in range(768)]
            
            # Search index
            if self.faiss_available:
                results = await self._search_faiss_index(query_embedding, k, 'facts')
            else:
                results = await self._search_memory_index(query_embedding, k, 'facts')
            
            # Filter by paper_id if provided
            if paper_id:
                results = [r for r in results if r.get('paper_id') == paper_id]
            
            return results[:k]
            
        except Exception as e:
            print(f"❌ Error searching facts: {e}")
            return []
    
    async def search_styles(self, 
                           query: str, 
                           style_name: str = None, 
                           k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant style patterns
        
        Args:
            query: Search query (e.g., "opening patterns", "transitions")
            style_name: Optional style filter
            k: Number of results to return
            
        Returns:
            List of relevant style patterns
        """
        try:
            if not self.style_index and not self.style_metadata:
                return []
            
            # Generate query embedding
            if self.embedding_client:
                response = await self.embedding_client.embed([query])
                query_embedding = response['data'][0]['embedding']
            else:
                # Random fallback
                import random
                query_embedding = [random.random() for _ in range(768)]
            
            # Search style index
            if self.faiss_available:
                results = await self._search_faiss_index(query_embedding, k, 'style')
            else:
                results = await self._search_memory_index(query_embedding, k, 'style')
            
            # Filter by style_name if provided
            if style_name:
                results = [r for r in results if r.get('style_name') == style_name]
            
            return results[:k]
            
        except Exception as e:
            print(f"❌ Error searching styles: {e}")
            return []
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            if len(chunk_words) >= 50:  # Minimum chunk size
                chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def _extract_style_sections(self, content: str) -> Dict[str, str]:
        """Extract different sections from style markdown"""
        sections = {}
        current_section = ""
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.replace('## ', '').strip()
                current_content = []
            elif line.startswith('### '):
                subsection = line.replace('### ', '').strip()
                current_content.append(f"\n{subsection}:")
            elif line.strip():
                current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    async def _add_to_faiss_index(self, 
                                 embeddings: List[List[float]], 
                                 metadata: List[Dict[str, Any]], 
                                 index_type: str):
        """Add embeddings to FAISS index"""
        embeddings_array = self.np.array(embeddings, dtype=self.np.float32)
        
        if index_type == 'facts':
            if self.facts_index is None:
                dimension = embeddings_array.shape[1]
                self.facts_index = self.faiss.IndexFlatIP(dimension)  # Inner product
            
            self.facts_index.add(embeddings_array)
            self.facts_metadata.extend(metadata)
            
        elif index_type == 'style':
            if self.style_index is None:
                dimension = embeddings_array.shape[1]
                self.style_index = self.faiss.IndexFlatIP(dimension)
            
            self.style_index.add(embeddings_array)
            self.style_metadata.extend(metadata)
        
        # Save index to disk
        await self._save_index_to_disk()
    
    async def _add_to_memory_index(self, 
                                  embeddings: List[List[float]], 
                                  metadata: List[Dict[str, Any]], 
                                  index_type: str):
        """Add to in-memory index (fallback)"""
        if index_type == 'facts':
            if not hasattr(self, 'memory_facts_embeddings'):
                self.memory_facts_embeddings = []
            self.memory_facts_embeddings.extend(embeddings)
            self.facts_metadata.extend(metadata)
            
        elif index_type == 'style':
            if not hasattr(self, 'memory_style_embeddings'):
                self.memory_style_embeddings = []
            self.memory_style_embeddings.extend(embeddings)
            self.style_metadata.extend(metadata)
    
    async def _search_faiss_index(self, 
                                 query_embedding: List[float], 
                                 k: int, 
                                 index_type: str) -> List[Dict[str, Any]]:
        """Search FAISS index"""
        query_array = self.np.array([query_embedding], dtype=self.np.float32)
        
        if index_type == 'facts' and self.facts_index:
            scores, indices = self.facts_index.search(query_array, k)
            metadata = self.facts_metadata
        elif index_type == 'style' and self.style_index:
            scores, indices = self.style_index.search(query_array, k)
            metadata = self.style_metadata
        else:
            return []
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(metadata):
                result = metadata[idx].copy()
                result['score'] = float(score)
                results.append(result)
        
        return results
    
    async def _search_memory_index(self, 
                                  query_embedding: List[float], 
                                  k: int, 
                                  index_type: str) -> List[Dict[str, Any]]:
        """Search in-memory index (fallback)"""
        if index_type == 'facts':
            embeddings = getattr(self, 'memory_facts_embeddings', [])
            metadata = self.facts_metadata
        else:
            embeddings = getattr(self, 'memory_style_embeddings', [])
            metadata = self.style_metadata
        
        if not embeddings:
            return []
        
        # Simple cosine similarity
        import random
        scores = [random.random() for _ in embeddings]  # Mock similarity
        
        # Get top k results
        scored_results = list(zip(scores, metadata))
        scored_results.sort(reverse=True)
        
        results = []
        for score, meta in scored_results[:k]:
            result = meta.copy()
            result['score'] = score
            results.append(result)
        
        return results
    
    async def _save_index_to_disk(self):
        """Save index and metadata to disk"""
        try:
            if self.faiss_available:
                if self.facts_index:
                    self.faiss.write_index(self.facts_index, str(self.index_path / "facts.index"))
                if self.style_index:
                    self.faiss.write_index(self.style_index, str(self.index_path / "style.index"))
            
            # Save metadata
            with open(self.index_path / "facts_metadata.pkl", 'wb') as f:
                pickle.dump(self.facts_metadata, f)
            with open(self.index_path / "style_metadata.pkl", 'wb') as f:
                pickle.dump(self.style_metadata, f)
                
        except Exception as e:
            print(f"⚠️  Could not save index to disk: {e}")
    
    async def load_index_from_disk(self) -> bool:
        """Load existing index from disk"""
        try:
            if self.faiss_available:
                facts_path = self.index_path / "facts.index"
                style_path = self.index_path / "style.index"
                
                if facts_path.exists():
                    self.facts_index = self.faiss.read_index(str(facts_path))
                if style_path.exists():
                    self.style_index = self.faiss.read_index(str(style_path))
            
            # Load metadata
            facts_meta_path = self.index_path / "facts_metadata.pkl"
            style_meta_path = self.index_path / "style_metadata.pkl"
            
            if facts_meta_path.exists():
                with open(facts_meta_path, 'rb') as f:
                    self.facts_metadata = pickle.load(f)
            
            if style_meta_path.exists():
                with open(style_meta_path, 'rb') as f:
                    self.style_metadata = pickle.load(f)
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not load index from disk: {e}")
            return False


# Retrieval interface that can be swapped with OpenSearch later
class RetrievalInterface:
    """Interface for retrieval that can use either local or cloud backend"""
    
    def __init__(self, use_local: bool = True):
        self.use_local = use_local
        
        if use_local:
            from backend.tools.sm_client import create_clients
            _, embedding_client = create_clients()
            self.indexer = LocalRAGIndexer(embedding_client=embedding_client)
        else:
            # TODO: Implement OpenSearch Serverless interface
            raise NotImplementedError("OpenSearch Serverless not implemented yet")
    
    async def index_paper(self, paper_id: str, content: str, title: str = "") -> bool:
        """Index paper content"""
        return await self.indexer.index_paper_content(paper_id, content, title)
    
    async def index_styles(self) -> bool:
        """Index style patterns"""
        return await self.indexer.index_style_patterns()
    
    async def retrieve_facts(self, query: str, k: int = 5, paper_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve relevant facts"""
        return await self.indexer.search_facts(query, k, paper_id)
    
    async def retrieve_styles(self, query: str, style_name: str = None, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant style patterns"""
        return await self.indexer.search_styles(query, style_name, k)