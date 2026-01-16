import unittest
from unittest.mock import MagicMock, patch
import json
import os
import shutil
import tempfile
from mcp_server.cache.semantic_cache import SemanticCache

class TestSemanticCache(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache file
        self.test_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.test_dir, "test_cache.json")
        
        # Mock genai
        self.genai_patcher = patch('mcp_server.cache.semantic_cache.genai')
        self.mock_genai = self.genai_patcher.start()
        
        # Setup mock embedding return
        self.mock_genai.embed_content.return_value = {'embedding': [1.0, 0.0, 0.0]}

    def tearDown(self):
        self.genai_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_store_and_lookup_exact_match(self):
        cache = SemanticCache(persistence_path=self.cache_path)
        
        tool = "test_tool"
        args = {"arg1": "value1"}
        result = {"data": "test_result"}
        
        # 1. Store
        cache.store(tool, args, result)
        
        # Verify it was stored in memory
        self.assertEqual(len(cache.cache), 1)
        self.assertEqual(cache.cache[0]['result'], result)
        
        # 2. Lookup (Exact Match - same embedding mocked)
        self.mock_genai.embed_content.return_value = {'embedding': [1.0, 0.0, 0.0]}
        cached = cache.lookup(tool, args)
        
        self.assertEqual(cached, result)

    def test_lookup_miss_low_similarity(self):
        cache = SemanticCache(persistence_path=self.cache_path)
        
        # Store an entry: Vector [1, 0, 0]
        self.mock_genai.embed_content.return_value = {'embedding': [1.0, 0.0, 0.0]}
        cache.store("test_tool", {"arg": "A"}, {"res": "A"})
        
        # Lookup with orthogonal vector [0, 1, 0] -> dot product 0
        self.mock_genai.embed_content.side_effect = [{'embedding': [0.0, 1.0, 0.0]}]
        
        cached = cache.lookup("test_tool", {"arg": "B"})
        self.assertIsNone(cached)

    def test_persistence(self):
        # 1. Create cache and store item
        cache1 = SemanticCache(persistence_path=self.cache_path)
        cache1.store("tool", {}, {"val": 1})
        
        # 2. Initialize new cache instance pointing to same file
        cache2 = SemanticCache(persistence_path=self.cache_path)
        
        # 3. Verify data loaded
        self.assertEqual(len(cache2.cache), 1)
        self.assertEqual(cache2.cache[0]['result'], {"val": 1})

if __name__ == '__main__':
    unittest.main()
