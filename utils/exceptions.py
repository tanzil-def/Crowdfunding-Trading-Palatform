from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.http import JsonResponse

class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data['status_code'] = response.status_code
        
        # Add request ID if available
        if hasattr(context['request'], 'id'):
            response.data['request_id'] = context['request'].id
    
    return response

def handler404(request, exception):
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'status_code': 404
    }, status=404)

def handler500(request):
    return JsonResponse({
        'error': 'Server Error',
        'message': 'An internal server error occurred.',
        'status_code': 500
    }, status=500)