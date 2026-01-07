from rest_framework import serializers
from .models import SharePurchase, PaymentTransaction

class InitiateInvestmentSerializer(serializers.Serializer):
    project_id = serializers.UUIDField()
    shares_requested = serializers.IntegerField()
    idempotency_key = serializers.CharField()

class PaymentCallbackSerializer(serializers.Serializer):
    payment_reference_id = serializers.CharField()
    success = serializers.BooleanField()
    gateway_payload = serializers.JSONField()

class SharePurchaseListSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title')

    class Meta:
        model = SharePurchase
        fields = (
            'id',
            'project',
            'project_title',
            'shares_purchased',
            'price_per_share',
            'total_amount',
            'created_at'
        )
