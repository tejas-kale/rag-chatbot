"""
Example integration of ChromaDB service with Flask application.
This file demonstrates how to use the ChromaDB service in the Flask app context.
"""

from flask import Flask, jsonify, request
from config import config
from chromadb_service import chromadb_service


def create_app_with_chromadb():
    """
    Create a Flask application with ChromaDB integration.
    
    This is an example of how to integrate the ChromaDB service
    with the existing Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    @app.route('/api/chromadb/collections', methods=['GET'])
    def list_collections():
        """List all ChromaDB collections."""
        try:
            collections = chromadb_service.list_collections()
            return jsonify({
                'collections': collections,
                'count': len(collections)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chromadb/collections/<collection_name>', methods=['POST'])
    def create_collection(collection_name):
        """Create a new ChromaDB collection."""
        try:
            metadata = request.json.get('metadata', {})
            collection = chromadb_service.get_or_create_collection(
                name=collection_name, 
                metadata=metadata
            )
            return jsonify({
                'message': f'Collection {collection_name} created/retrieved successfully',
                'name': collection.name
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chromadb/collections/<collection_name>/documents', methods=['POST'])
    def add_documents(collection_name):
        """Add documents to a ChromaDB collection."""
        try:
            data = request.json
            documents = data.get('documents', [])
            metadatas = data.get('metadatas', None)
            ids = data.get('ids', None)
            
            if not documents:
                return jsonify({'error': 'Documents are required'}), 400
            
            success = chromadb_service.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                count = chromadb_service.get_collection_count(collection_name)
                return jsonify({
                    'message': f'Added {len(documents)} documents to {collection_name}',
                    'total_documents': count
                })
            else:
                return jsonify({'error': 'Failed to add documents'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chromadb/collections/<collection_name>/search', methods=['POST'])
    def search_documents(collection_name):
        """Search documents in a ChromaDB collection."""
        try:
            data = request.json
            query_text = data.get('query', '')
            n_results = data.get('n_results', 10)
            where = data.get('where', None)
            
            if not query_text:
                return jsonify({'error': 'Query text is required'}), 400
            
            results = chromadb_service.query_documents(
                collection_name=collection_name,
                query_texts=query_text,
                n_results=n_results,
                where=where
            )
            
            if results:
                return jsonify({
                    'results': results,
                    'query': query_text
                })
            else:
                return jsonify({'error': 'Search failed'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chromadb/collections/<collection_name>', methods=['DELETE'])
    def delete_collection(collection_name):
        """Delete a ChromaDB collection."""
        try:
            success = chromadb_service.delete_collection(collection_name)
            if success:
                return jsonify({
                    'message': f'Collection {collection_name} deleted successfully'
                })
            else:
                return jsonify({'error': 'Failed to delete collection'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/chromadb/status', methods=['GET'])
    def chromadb_status():
        """Get ChromaDB status and configuration."""
        try:
            collections = chromadb_service.list_collections()
            return jsonify({
                'status': 'healthy',
                'persist_path': app.config.get('CHROMADB_PERSIST_PATH'),
                'collections': collections,
                'collection_count': len(collections)
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    return app


if __name__ == '__main__':
    app = create_app_with_chromadb()
    app.run(debug=True)