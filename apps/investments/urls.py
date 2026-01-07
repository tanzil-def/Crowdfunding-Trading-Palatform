from django.urls import path
from .views import InvestmentInitiateView, PaymentCallbackView, MyInvestmentsListView

app_name = 'investments'

urlpatterns = [
    # Initiate investment
    path('initiate/', InvestmentInitiateView.as_view(), name='investment-initiate'),

    # Payment callback (standardized)
    path('payments/callback/', PaymentCallbackView.as_view(), name='payment-callback'),

    # Investor's investments
    path('my/', MyInvestmentsListView.as_view(), name='my-investments'),
]
