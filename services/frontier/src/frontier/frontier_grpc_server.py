import grpc 
import shared.protos.frontier.frontier_pb2 as frontier__pb2
import shared.protos.frontier.frontier_pb2_grpc as frontier_pb2_grpc
from typing import override
from concurrent import futures

class CrawlServicer(frontier_pb2_grpc.FrontierServiceServicer):
    @override
    def CrawlRequest(self, request: frontier__pb2.FrontierRequest, context: grpc.ServicerContext) -> frontier__pb2.FrontierResponse: # pyright: ignore[reportAttributeAccessIssue]
        # Rest will be handled by the worker master when it reads the crawl request from the queue
        print(f"Received crawl request for URL: {request.url} and {request.depth} depth")
        return frontier__pb2.FrontierResponse(status="queued") # type: ignore

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    frontier_pb2_grpc.add_FrontierServiceServicer_to_server(CrawlServicer(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    
    print("Frontier gRPC server started on port 50051")

    server.wait_for_termination()
