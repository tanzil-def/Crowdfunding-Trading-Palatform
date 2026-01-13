from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    Standardized success response format.
    
    Returns:
        {
            "success": true,
            "message": "Success message",
            "data": {...}
        }
    """
    response_data = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response_data["data"] = data
    
    return Response(response_data, status=status_code)


def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standardized error response format.
    
    Returns:
        {
            "success": false,
            "message": "Error message",
            "errors": {...}  # optional
        }
    """
    response_data = {
        "success": False,
        "message": message
    }
    
    if errors is not None:
        response_data["errors"] = errors
    
    return Response(response_data, status=status_code)