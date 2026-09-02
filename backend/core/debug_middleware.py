import json
import logging

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.error(f"=== {request.path} START ===")
        logger.error(f"Method: {request.method}")
        logger.error(f"Path: {request.path}")
        
        user = getattr(request, 'user', None)
        logger.error(f"User: {user}")
        logger.error(f"User authenticated: {getattr(user, 'is_authenticated', 'N/A') if user else 'No user'}")
        logger.error(f"Headers: {dict(request.headers)}")
        
        if request.body:
            try:
                body = json.loads(request.body.decode('utf-8'))
                logger.error(f"Body: {body}")
            except Exception as e:
                logger.error(f"Body parse error: {e}")
                logger.error(f"Raw body: {request.body}")

        response = self.get_response(request)
        
        logger.error(f"Response status: {response.status_code}")
        if hasattr(response, 'content'):
            try:
                content = response.content.decode('utf-8')
                logger.error(f"Response content: {content}")
            except:
                logger.error(f"Response content (raw): {response.content}")
        logger.error(f"=== {request.path} END ===")

        return response