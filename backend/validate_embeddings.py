"""
Simple validation script for embedding configuration.
Tests the basic structure and logic without requiring external dependencies.
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_structure():
    """Test that config.py has the required embedding configuration."""
    print("Testing config structure...")
    
    try:
        # Import config module
        from config import Config
        
        # Check that required attributes exist
        required_attrs = [
            'EMBEDDING_PROVIDER',
            'EMBEDDING_MODEL', 
            'OPENAI_API_KEY',
            'HUGGINGFACE_API_TOKEN'
        ]
        
        for attr in required_attrs:
            if not hasattr(Config, attr):
                print(f"✗ Missing required config attribute: {attr}")
                return False
            print(f"✓ Found config attribute: {attr}")
        
        print("✓ Config structure test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing config: {e}")
        return False


def test_embeddings_structure():
    """Test that embeddings.py has the required structure."""
    print("\nTesting embeddings module structure...")
    
    try:
        # Import embeddings module
        import embeddings
        
        # Check that required classes and functions exist
        required_items = [
            'EmbeddingFactory',
            'get_default_embedding_model',
            'create_embedding_function'
        ]
        
        for item in required_items:
            if not hasattr(embeddings, item):
                print(f"✗ Missing required item: {item}")
                return False
            print(f"✓ Found item: {item}")
        
        # Check EmbeddingFactory class structure
        factory = embeddings.EmbeddingFactory
        required_methods = [
            'create_embedding_model',
            '_create_huggingface_embedding',
            '_create_openai_embedding'
        ]
        
        for method in required_methods:
            if not hasattr(factory, method):
                print(f"✗ Missing required method: {method}")
                return False
            print(f"✓ Found method: {method}")
        
        # Check supported providers
        if not hasattr(factory, 'SUPPORTED_PROVIDERS'):
            print("✗ Missing SUPPORTED_PROVIDERS attribute")
            return False
        
        expected_providers = ['huggingface', 'openai']
        if factory.SUPPORTED_PROVIDERS != expected_providers:
            print(f"✗ Unexpected providers: {factory.SUPPORTED_PROVIDERS}")
            return False
        
        print("✓ Embeddings structure test passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import embeddings: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing embeddings: {e}")
        return False


def test_env_example_updated():
    """Test that .env.example has been updated with embedding variables."""
    print("\nTesting .env.example updates...")
    
    try:
        env_example_path = '.env.example'
        if not os.path.exists(env_example_path):
            print("✗ .env.example file not found")
            return False
        
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        required_vars = [
            'EMBEDDING_PROVIDER',
            'EMBEDDING_MODEL',
            'OPENAI_API_KEY',
            'HUGGINGFACE_API_TOKEN'
        ]
        
        for var in required_vars:
            if var not in content:
                print(f"✗ Missing environment variable: {var}")
                return False
            print(f"✓ Found environment variable: {var}")
        
        print("✓ Environment example test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing .env.example: {e}")
        return False


def test_pyproject_dependencies():
    """Test that pyproject.toml has been updated with LangChain dependencies."""
    print("\nTesting pyproject.toml dependencies...")
    
    try:
        pyproject_path = 'pyproject.toml'
        if not os.path.exists(pyproject_path):
            print("✗ pyproject.toml file not found")
            return False
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        required_deps = [
            'langchain',
            'langchain-community',
            'langchain-openai',
            'langchain-huggingface'
        ]
        
        for dep in required_deps:
            if dep not in content:
                print(f"✗ Missing dependency: {dep}")
                return False
            print(f"✓ Found dependency: {dep}")
        
        print("✓ Dependencies test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing pyproject.toml: {e}")
        return False


def main():
    """Run all validation tests."""
    print("Running embedding configuration validation tests...\n")
    
    tests = [
        test_config_structure,
        test_embeddings_structure,
        test_env_example_updated,
        test_pyproject_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All validation tests passed! Embedding configuration is ready.")
        return True
    else:
        print("✗ Some validation tests failed. Please check the implementation.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)