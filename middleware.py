import time
import logging
from fastapi import Request

logger = logging.getLogger("api")


async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()

    # get client ip and requests details
    client_host = request.client.host if request.client else "unknown"
    request_path = request.url.path
    request_method = request.method

    logger.info(f"Start request: {request_method} {request_path} from {client_host}")

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = round((time.time() - start_time) * 1000)

    # Log completion with status code and time
    logger.warning(
        f"Complete: {request_method} {request_path} - Status: {response.status_code} - Time: {process_time}ms"
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response
