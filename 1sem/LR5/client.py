import grpc
import logging

import glossary_pb2
import glossary_pb2_grpc


class GlossaryClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = glossary_pb2_grpc.GlossaryServiceStub(self.channel)
        logging.info(f"Connected to gRPC server at {host}:{port}")

    def list_terms(self, skip=0, limit=100):
        """Get all terms"""
        try:
            request = glossary_pb2.ListTermsRequest(skip=skip, limit=limit)
            response = self.stub.ListTerms(request)
            return response
        except grpc.RpcError as e:
            logging.error(f"gRPC error: {e.code()} - {e.details()}")
            return None

    def get_term(self, keyword):
        """Get term by keyword"""
        try:
            request = glossary_pb2.GetTermRequest(keyword=keyword)
            response = self.stub.GetTerm(request)
            return response
        except grpc.RpcError as e:
            logging.error(f"gRPC error: {e.code()} - {e.details()}")
            return None

    def create_term(self, keyword, description, category="general"):
        """Create a new term"""
        try:
            request = glossary_pb2.CreateTermRequest(
                keyword=keyword,
                description=description,
                category=category
            )
            response = self.stub.CreateTerm(request)
            return response
        except grpc.RpcError as e:
            logging.error(f"gRPC error: {e.code()} - {e.details()}")
            return None

    def update_term(self, keyword, description=None, category=None):
        """Update a term"""
        try:
            request = glossary_pb2.UpdateTermRequest(keyword=keyword)
            if description:
                request.description = description
            if category:
                request.category = category

            response = self.stub.UpdateTerm(request)
            return response
        except grpc.RpcError as e:
            logging.error(f"gRPC error: {e.code()} - {e.details()}")
            return None

    def delete_term(self, keyword):
        """Delete a term"""
        try:
            request = glossary_pb2.DeleteTermRequest(keyword=keyword)
            response = self.stub.DeleteTerm(request)
            return response
        except grpc.RpcError as e:
            logging.error(f"gRPC error: {e.code()} - {e.details()}")
            return None


def demo_client():
    """Demo client usage"""
    logging.basicConfig(level=logging.INFO)
    client = GlossaryClient()

    print("=== Python Glossary gRPC Client Demo ===")

    # 1. List all terms
    print("\n1. All terms:")
    response = client.list_terms()
    if response:
        for term in response.terms:
            print(f"   - {term.keyword} ({term.category})")

    # 2. Get specific term
    print("\n2. Get term 'Функция':")
    term = client.get_term("Функция")
    if term and term.keyword:
        print(f"   {term.keyword}: {term.description}")

    # 3. Create new term
    print("\n3. Create term 'Кортеж':")
    new_term = client.create_term(
        keyword="Кортеж",
        description="Неизменяемая последовательность элементов",
        category="data_structures"
    )
    if new_term and new_term.keyword:
        print(f"Created: {new_term.keyword}")

    # 4. List terms again to see the new one
    print("\n4. Updated terms list:")
    response = client.list_terms()
    if response:
        for term in response.terms:
            print(term.keyword)


if __name__ == "__main__":
    demo_client()