- Queue Details Crawl Requests:
  - Exchange Name: 'crawl_requests'
  - Queue Name: 'crawl_requests_queue'
  - Routing Key: 'crawl_requests'
  
- Per Worker:
  - Exchange Name: 'worker_{WORKER_ID}'
  - Queue Name: 'worker_{WORKER_ID}_queue'
  - Routing Key: 'worker_{WORKER_ID}_task'
  
  
## GRPC Servers:
 - Frontier Service:
   - Host: 'localhost'
   - Port: 50051
   
 - Master Service:
   - Host: 'localhost'
   - Port: 50052
   