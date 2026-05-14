"""
Gateway Request Context Middleware (app/core/middleware.py)

Purpose:
    Runs on every incoming request before any route handler is called.
    Stamps each request with a unique UUID for distributed tracing.

What it does:
    1. Generates a UUID4 string as request_id.
    2. Attaches it to request.state.request_id — accessible in all route handlers.
    3. Passes control to the next handler (route or next middleware) via call_next().
    4. After the response is built, adds x-request-id to the response headers
       so clients and logs can correlate requests.

Why this matters:
    In a distributed system, a single user action touches multiple services.
    When something fails, you need to find that one request across all service logs.
    The request_id travels with the request to every downstream service
    (passed as x-request-id header in routes.py). Search any log by this ID
    to reconstruct the full journey of a request.

Registered in main.py as:
    app.middleware("http")(add_request_context)
"""

import uuid
from fastapi import Request


async def add_request_context(request: Request, call_next):
    """
    Attach request_id to every incoming request.
    """

    request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["x-request-id"] = request_id

    return response