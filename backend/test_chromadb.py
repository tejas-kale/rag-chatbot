"""
Test script for ChromaDB service.
This script tests the basic functionality of the ChromaDB service.
"""

import os
import sys
import tempfile
import shutil
import traceback
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import config
from chromadb_service import ChromaDBService


def test_chromadb_service():
    """Test the ChromaDB service functionality."""
    print("Testing ChromaDB Service...")
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Create a test Flask app
        app = Flask(__name__)
        app.config.from_object(config['testing'])
        app.config['CHROMADB_PERSIST_PATH'] = os.path.join(temp_dir, 'test_chroma')
        
        with app.app_context():
            # Initialize the service
            service = ChromaDBService()
            
            # Test 1: Create a collection
            print("\nTest 1: Creating a collection...")
            collection = service.get_or_create_collection("test_collection")
            assert collection is not None
            print("✓ Collection created successfully")
            
            # Test 2: List collections
            print("\nTest 2: Listing collections...")
            collections = service.list_collections()
            assert "test_collection" in collections
            print(f"✓ Collections found: {collections}")
            
            # Test 3: Add documents
            print("\nTest 3: Adding documents...")
            documents = [
                "This is the first test document about artificial intelligence.",
                "This is the second document discussing machine learning.",
                "The third document covers natural language processing."
            ]
            metadatas = [
                {"topic": "AI", "source": "test"},
                {"topic": "ML", "source": "test"},
                {"topic": "NLP", "source": "test"}
            ]
            
            success = service.add_documents(
                collection_name="test_collection",
                documents=documents,
                metadatas=metadatas,
                ids=["doc1", "doc2", "doc3"]
            )
            assert success
            print("✓ Documents added successfully")
            
            # Test 4: Get collection count
            print("\nTest 4: Getting collection count...")
            count = service.get_collection_count("test_collection")
            assert count == 3
            print(f"✓ Collection count: {count}")
            
            # Test 5: Query documents
            print("\nTest 5: Querying documents...")
            results = service.query_documents(
                collection_name="test_collection",
                query_texts="artificial intelligence",
                n_results=2
            )
            assert results is not None
            assert len(results['ids'][0]) <= 2
            print(f"✓ Query returned {len(results['ids'][0])} results")
            print(f"  Top result: {results['documents'][0][0][:50]}...")
            
            # Test 6: Query with metadata filter
            print("\nTest 6: Querying with metadata filter...")
            results = service.query_documents(
                collection_name="test_collection",
                query_texts="learning",
                n_results=5,
                where={"topic": "ML"}
            )
            assert results is not None
            print(f"✓ Filtered query returned {len(results['ids'][0])} results")
            
            # Test 7: Delete collection
            print("\nTest 7: Deleting collection...")
            success = service.delete_collection("test_collection")
            assert success
            collections = service.list_collections()
            assert "test_collection" not in collections
            print("✓ Collection deleted successfully")
            
            print("\n🎉 All tests passed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
    
    return True


if __name__ == "__main__":
    success = test_chromadb_service()
    sys.exit(0 if success else 1)