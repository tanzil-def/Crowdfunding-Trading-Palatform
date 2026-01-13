from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestmentViewSet, PaymentTransactionViewSet

router = DefaultRouter()
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'payments', PaymentTransactionViewSet, basename='payment')

app_name = 'investments'

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints for specific functionality
    path('investments/<uuid:pk>/initiate-payment/', 
         InvestmentViewSet.as_view({'post': 'initiate_payment'}), 
         name='initiate-payment'),
    
    path('investments/<uuid:pk>/review/', 
         InvestmentViewSet.as_view({'post': 'review'}), 
         name='review-investment'),
    
    path('investments/<uuid:pk>/cancel/', 
         InvestmentViewSet.as_view({'post': 'cancel'}), 
         name='cancel-investment'),
    
    path('investments/my/portfolio/', 
         InvestmentViewSet.as_view({'get': 'portfolio'}), 
         name='my-portfolio'),
]