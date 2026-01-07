from django.urls import path
from .views import InvestmentInitiateView, PaymentCallbackView, MyInvestmentsListView

urlpatterns = [
    path('initiate/', InvestmentInitiateView.as_view(), name='investment-initiate'),
    path('callback/', PaymentCallbackView.as_view(), name='payment-callback'),
    path('my/', MyInvestmentsListView.as_view(), name='my-investments'),
]

