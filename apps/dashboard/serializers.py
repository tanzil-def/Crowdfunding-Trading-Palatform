from rest_framework import serializers

class DeveloperDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    total_shares_sold = serializers.IntegerField()
    total_investment_received = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_projects = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()

class InvestorDashboardSerializer(serializers.Serializer):
    total_investments = serializers.IntegerField()
    portfolio_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    favorite_projects = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()

class AdminDashboardSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    pending_projects = serializers.IntegerField()
    total_investments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    unread_notifications = serializers.IntegerField()
