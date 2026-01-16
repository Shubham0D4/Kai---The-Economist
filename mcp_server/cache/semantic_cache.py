import os
import json
import logging
import numpy as np
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "cache_data.json")

class SemanticCache:
    def __init__(self, persistence_path: str = CACHE_FILE_PATH):
        """
        Initialize the Semantic Cache.
        
        Args:
            persistence_path: Path to the JSON file for persisting cache data.
        """
        self.persistence_path = persistence_path
        self.cache: List[Dict[str, Any]] = []
        self._load_cache()
        
        # Configure Google GenAI
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. Semantic Cache will not function correctly for embeddings.")
        else:
            genai.configure(api_key=api_key)

    def _load_cache(self):
        """Load cache from disk."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} entries from cache.")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = []

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.persistence_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info("Cache saved to disk.")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for the given text using Google GenAI.
        """
        try:
            model = "models/text-embedding-004"
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(v1, v2) / (norm1 * norm2)

    def lookup(self, tool_name: str, arguments: Dict[str, Any], threshold: float = 0.90) -> Optional[Dict[str, Any]]:
        """
        Look up a query in the cache based on semantic similarity.
        
        Args:
            tool_name: Name of the tool being called.
            arguments: Arguments passed to the tool.
            threshold: Similarity threshold (0.0 to 1.0).
            
        Returns:
            Cached result if found, None otherwise.
        """
        # Construct a query string representing the intent
        query_text = f"Tool: {tool_name}, Args: {json.dumps(arguments, sort_keys=True)}"
        
        embedding = self._get_embedding(query_text)
        if not embedding:
            return None

        best_match = None
        highest_similarity = -1.0

        for entry in self.cache:
            # Filter by tool name to narrow down search (optional but good for precision)
            if entry.get("tool") != tool_name:
                continue
                
            entry_embedding = entry.get("embedding")
            if not entry_embedding:
                continue
                
            similarity = self._cosine_similarity(embedding, entry_embedding)
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = entry

        if highest_similarity >= threshold and best_match:
            logger.info(f"Cache HIT! Similarity: {highest_similarity:.4f}")
            return best_match["result"]
        
        logger.info(f"Cache MISS. Best similarity: {highest_similarity:.4f}")
        return None

    def store(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """
        Store a result in the cache.
        
        Args:
            tool_name: Name of the tool.
            arguments: Arguments used.
            result: Result to cache.
        """
        query_text = f"Tool: {tool_name}, Args: {json.dumps(arguments, sort_keys=True)}"
        
        embedding = self._get_embedding(query_text)
        if not embedding:
            logger.warning("Could not generate embedding, skipping cache store.")
            return

        entry = {
            "tool": tool_name,
            "query_text": query_text,
            "arguments": arguments,
            "embedding": embedding,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.cache.append(entry)
        self._save_cache()
