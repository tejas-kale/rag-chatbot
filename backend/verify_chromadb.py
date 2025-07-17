#!/usr/bin/env python3
"""
Manual verification script for ChromaDB integration.
This script demonstrates the ChromaDB functionality and can be used to verify
the implementation when ChromaDB is properly installed.

Usage:
    python verify_chromadb.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_chromadb_installation():
    """Verify that ChromaDB can be imported."""
    try:
        import chromadb
        print(f"✓ ChromaDB version {chromadb.__version__} is available")
        return True
    except ImportError:
        print("❌ ChromaDB is not installed")
        print("   Install with: pip install chromadb")
        return False


def verify_flask_dependencies():
    """Verify Flask dependencies are available."""
    try:
        import flask
        print(f"✓ Flask is available")
        return True
    except ImportError:
        print("❌ Flask is not installed")
        return False


def run_chromadb_integration_test():
    """Run the full ChromaDB integration test."""
    print("\n" + "="*50)
    print("CHROMADB INTEGRATION VERIFICATION")
    print("="*50)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    chromadb_ok = verify_chromadb_installation()
    flask_ok = verify_flask_dependencies()
    
    if not (chromadb_ok and flask_ok):
        print("\n❌ Missing dependencies - cannot run full test")
        print("\nTo install dependencies:")
        print("pip install chromadb flask python-dotenv")
        return False
    
    # Run the actual test
    print("\n2. Running ChromaDB service test...")
    try:
        from test_chromadb import test_chromadb_service
        success = test_chromadb_service()
        
        if success:
            print("\n3. Running Flask integration test...")
            test_flask_integration()
            
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flask_integration():
    """Test the Flask integration example."""
    try:
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # Set up Flask app with ChromaDB
        os.environ['CHROMADB_PERSIST_PATH'] = os.path.join(temp_dir, 'test_chroma')
        
        from chromadb_example import create_app_with_chromadb
        app = create_app_with_chromadb()
        
        with app.test_client() as client:
            # Test status endpoint
            response = client.get('/api/chromadb/status')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            print("✓ Flask integration: Status endpoint works")
            
            # Test collection creation
            response = client.post('/api/chromadb/collections/test_collection')
            assert response.status_code == 200
            print("✓ Flask integration: Collection creation works")
            
            # Test document addition
            response = client.post('/api/chromadb/collections/test_collection/documents', 
                                 json={
                                     'documents': ['Test document about AI'],
                                     'ids': ['test_doc_1']
                                 })
            assert response.status_code == 200
            print("✓ Flask integration: Document addition works")
            
            # Test search
            response = client.post('/api/chromadb/collections/test_collection/search',
                                 json={'query': 'artificial intelligence'})
            assert response.status_code == 200
            print("✓ Flask integration: Document search works")
            
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        print("✓ Flask integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Flask integration test failed: {e}")
        raise


def main():
    """Main verification function."""
    print("ChromaDB Integration Verification Tool")
    print("This tool verifies that the ChromaDB integration is working correctly.")
    
    try:
        success = run_chromadb_integration_test()
        
        if success:
            print("\n" + "="*50)
            print("🎉 ALL TESTS PASSED!")
            print("✓ ChromaDB integration is working correctly")
            print("✓ Persistence is configured properly")
            print("✓ Flask integration is functional")
            print("\nThe ChromaDB vector store is ready for use!")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("❌ SOME TESTS FAILED")
            print("Please check the error messages above.")
            print("="*50)
            
        return success
        
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)