import grpc
from concurrent import futures
import logging
import sys
from flask import Flask, jsonify, request

sys.path.append('/app')

from database import GlossaryDatabase
import glossary_pb2
import glossary_pb2_grpc

logger = logging.getLogger(__name__)


class GlossaryService(glossary_pb2_grpc.GlossaryServiceServicer):
    def __init__(self):
        self.db = GlossaryDatabase()
        logger.info("GlossaryService initialized")

    def ListTerms(self, request, context):
        """Get list of all terms"""
        try:
            skip = request.skip if request.skip else 0
            limit = request.limit if request.limit else 100

            terms, total_count = self.db.list_terms(skip=skip, limit=limit)

            term_responses = []
            for term in terms:
                term_responses.append(glossary_pb2.TermResponse(
                    keyword=term['keyword'],
                    description=term['description'],
                    category=term['category']
                ))

            return glossary_pb2.ListTermsResponse(
                terms=term_responses,
                total_count=total_count
            )

        except Exception as e:
            logger.error(f"Error in ListTerms: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return glossary_pb2.ListTermsResponse()

    def GetTerm(self, request, context):
        """Get term by keyword"""
        try:
            if not request.keyword:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Keyword is required")
                return glossary_pb2.TermResponse()

            term = self.db.get_term(request.keyword)

            if not term:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Term '{request.keyword}' not found")
                return glossary_pb2.TermResponse()

            return glossary_pb2.TermResponse(
                keyword=term['keyword'],
                description=term['description'],
                category=term['category']
            )

        except Exception as e:
            logger.error(f"Error in GetTerm: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return glossary_pb2.TermResponse()

    def CreateTerm(self, request, context):
        """Create a new term"""
        try:
            if not request.keyword or not request.description:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Keyword and description are required")
                return glossary_pb2.TermResponse()

            success = self.db.create_term(
                keyword=request.keyword,
                description=request.description,
                category=request.category or "general"
            )

            if not success:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details(f"Term '{request.keyword}' already exists")
                return glossary_pb2.TermResponse()

            term = self.db.get_term(request.keyword)
            return glossary_pb2.TermResponse(
                keyword=term['keyword'],
                description=term['description'],
                category=term['category']
            )

        except Exception as e:
            logger.error(f"Error in CreateTerm: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return glossary_pb2.TermResponse()

    def UpdateTerm(self, request, context):
        """Update an existing term"""
        try:
            if not request.keyword:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Keyword is required")
                return glossary_pb2.TermResponse()

            existing_term = self.db.get_term(request.keyword)
            if not existing_term:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Term '{request.keyword}' not found")
                return glossary_pb2.TermResponse()

            success = self.db.update_term(
                keyword=request.keyword,
                description=request.description if request.description else None,
                category=request.category if request.category else None
            )

            if not success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to update term")
                return glossary_pb2.TermResponse()

            term = self.db.get_term(request.keyword)
            return glossary_pb2.TermResponse(
                keyword=term['keyword'],
                description=term['description'],
                category=term['category']
            )

        except Exception as e:
            logger.error(f"Error in UpdateTerm: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return glossary_pb2.TermResponse()

    def DeleteTerm(self, request, context):
        """Delete a term"""
        try:
            if not request.keyword:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Keyword is required")
                return glossary_pb2.DeleteResponse(success=False, message="Keyword required")

            success = self.db.delete_term(request.keyword)

            if not success:
                return glossary_pb2.DeleteResponse(
                    success=False,
                    message=f"Term '{request.keyword}' not found"
                )

            return glossary_pb2.DeleteResponse(
                success=True,
                message=f"Term '{request.keyword}' deleted successfully"
            )

        except Exception as e:
            logger.error(f"Error in DeleteTerm: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return glossary_pb2.DeleteResponse(success=False, message=str(e))


def start_grpc_server():
    """Запуск gRPC сервера в отдельном потоке"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    glossary_pb2_grpc.add_GlossaryServiceServicer_to_server(GlossaryService(), server)

    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    logger.info(f"✅ gRPC Server started on port {port}")
    return server


def start_flask_app():
    """Запуск Flask Web API"""
    app = Flask(__name__)

    # Создаем gRPC клиент для Web API
    channel = grpc.insecure_channel('localhost:50051')
    stub = glossary_pb2_grpc.GlossaryServiceStub(channel)

    @app.route('/')
    def home():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Python Glossary - Web API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .term { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .button { background: #007cba; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
                .button:hover { background: #005a87; }
            </style>
        </head>
        <body>
            <h1>📚 Python Glossary gRPC Service</h1>
            <p>This service provides both gRPC and REST API access to Python terminology.</p>

            <h2>Web Interface</h2>
            <p><a href="/terms" class="button">View All Terms (JSON)</a></p>
            <p><a href="/terms/REST" class="button">View REST Term</a></p>
            <p><a href="/terms/RPC" class="button">View RPC Term</a></p>

            <h2>REST API Endpoints</h2>
            <div class="term">
                <strong>GET /terms</strong> - Get all terms<br>
                <strong>GET /terms/&lt;keyword&gt;</strong> - Get specific term<br>
                <strong>POST /terms</strong> - Create new term (use JSON)<br>
                <strong>PUT /terms/&lt;keyword&gt;</strong> - Update term (use JSON)<br>
                <strong>DELETE /terms/&lt;keyword&gt;</strong> - Delete term
            </div>

            <h2>gRPC Service</h2>
            <p>gRPC server is running on port 50051</p>
        </body>
        </html>
        '''

    @app.route('/terms', methods=['GET'])
    def get_all_terms():
        """Получение списка всех терминов"""
        try:
            response = stub.ListTerms(glossary_pb2.ListTermsRequest())
            terms = [{
                "keyword": term.keyword,
                "description": term.description,
                "category": term.category
            } for term in response.terms]
            return jsonify(terms)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/terms/<keyword>', methods=['GET'])
    def get_term(keyword):
        """Получение информации о конкретном термине"""
        try:
            response = stub.GetTerm(glossary_pb2.GetTermRequest(keyword=keyword))
            return jsonify({
                "keyword": response.keyword,
                "description": response.description,
                "category": response.category
            })
        except Exception as e:
            return jsonify({"error": "Term not found"}), 404

    @app.route('/terms', methods=['POST'])
    def create_term():
        """Добавление нового термина с описанием"""
        data = request.get_json()
        if not data or 'keyword' not in data or 'description' not in data:
            return jsonify({"error": "Keyword and description are required"}), 400

        try:
            response = stub.CreateTerm(glossary_pb2.CreateTermRequest(
                keyword=data['keyword'],
                description=data['description'],
                category=data.get('category', 'general')
            ))
            return jsonify({
                "keyword": response.keyword,
                "description": response.description,
                "category": response.category
            }), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/terms/<keyword>', methods=['PUT'])
    def update_term(keyword):
        """Обновление существующего термина"""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            response = stub.UpdateTerm(glossary_pb2.UpdateTermRequest(
                keyword=keyword,
                description=data.get('description', ''),
                category=data.get('category', '')
            ))
            return jsonify({
                "keyword": response.keyword,
                "description": response.description,
                "category": response.category
            })
        except Exception as e:
            return jsonify({"error": "Term not found"}), 404

    @app.route('/terms/<keyword>', methods=['DELETE'])
    def delete_term(keyword):
        """Удаление термина из глоссария"""
        try:
            response = stub.DeleteTerm(glossary_pb2.DeleteTermRequest(keyword=keyword))
            return jsonify({
                "success": response.success,
                "message": response.message
            })
        except Exception as e:
            return jsonify({"error": "Term not found"}), 404

    logger.info("✅ Flask Web API started on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)


def serve():
    """Запуск обоих серверов"""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Python Glossary Service...")

    # Запускаем gRPC сервер в отдельном потоке
    grpc_server = start_grpc_server()

    # Запускаем Flask Web API в основном потоке
    start_flask_app()

    grpc_server.wait_for_termination()


if __name__ == "__main__":
    serve()