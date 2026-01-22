from rest_framework.renderers import JSONRenderer

class StandardizedRenderer(JSONRenderer):
    """
    Custom renderer to ensure all API responses follow the standard format:
    {
        "success": bool,
        "message": str,
        "data": obj or null
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        
        # If it's already in our standard format, just render it
        if isinstance(data, dict) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)
            
        # Determine success status from HTTP response code
        success = True
        if response and response.status_code >= 400:
            success = False
            
        message = "Success"
        if not success:
            message = "Error"
            
        # Handle DRF error messages and details
        if isinstance(data, dict):
            if 'detail' in data:
                message = data.pop('detail')
            elif 'message' in data and len(data) == 1:
                message = data.pop('message')

        # Wrap the data
        wrapped_data = {
            "success": success,
            "message": message,
            "data": data
        }
        
        # If it's an error, data should be in 'errors' field or null
        if not success:
            wrapped_data["errors"] = data
            wrapped_data["data"] = None

        return super().render(wrapped_data, accepted_media_type, renderer_context)
