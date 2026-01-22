from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Developer Dashboard Example',
            value={
                "total_projects": 8,
                "total_shares_sold": 2500,
                "total_investment_received": "950000.00",
                "pending_projects": 3,
                "unread_notifications": 5
            }
        )
    ]
)
class DeveloperDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField(min_value=0, help_text="Total projects (e.g. 5)")
    total_shares_sold = serializers.IntegerField(min_value=0, help_text="Total shares sold (e.g. 1200)")
    total_investment_received = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, help_text="Total investment received (e.g. 450000.00)")
    pending_projects = serializers.IntegerField(min_value=0, help_text="Pending projects (e.g. 2)")
    unread_notifications = serializers.IntegerField(min_value=0, help_text="Unread notifications (e.g. 3)")

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Investor Dashboard Example',
            value={
                "total_investments": 15,
                "portfolio_value": "425000.75",
                "favorite_projects": 9,
                "unread_notifications": 2
            }
        )
    ]
)
class InvestorDashboardSerializer(serializers.Serializer):
    total_investments = serializers.IntegerField(min_value=0, help_text="Total investments (e.g. 12)")
    portfolio_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, help_text="Portfolio value (e.g. 320000.50)")
    favorite_projects = serializers.IntegerField(min_value=0, help_text="Favorite projects (e.g. 8)")
    unread_notifications = serializers.IntegerField(min_value=0, help_text="Unread notifications (e.g. 1)")

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Admin Dashboard Example',
            value={
                "total_projects": 120,
                "pending_projects": 15,
                "total_investments": 850,
                "total_revenue": "1250000.00",
                "unread_notifications": 42
            }
        )
    ]
)
class AdminDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField(min_value=0, help_text="Total projects (e.g. 45)")
    pending_projects = serializers.IntegerField(min_value=0, help_text="Pending projects (e.g. 7)")
    total_investments = serializers.IntegerField(min_value=0, help_text="Total investments (e.g. 156)")
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, help_text="Total revenue (e.g. 150000.00)")
    unread_notifications = serializers.IntegerField(min_value=0, help_text="Unread notifications (e.g. 12)")
