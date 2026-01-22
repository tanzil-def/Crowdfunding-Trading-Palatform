from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from decimal import Decimal
import uuid

User = get_user_model()

class InvestmentTests(APITestCase):
    def setUp(self):
        self.investor = User.objects.create_user(
            email=f'inv_{uuid.uuid4()}@example.com', 
            password='password123', 
            first_name='Inv',
            last_name='User',
            role='INVESTOR', 
            is_active=True,
            is_email_verified=True
        )
        self.unverified_investor = User.objects.create_user(
            email=f'unv_{uuid.uuid4()}@example.com', 
            password='password123', 
            first_name='Unv',
            last_name='User',
            role='INVESTOR', 
            is_active=True,
            is_email_verified=False
        )
        self.developer = User.objects.create_user(
            email=f'dev_{uuid.uuid4()}@example.com', 
            password='password123',
            first_name='Dev',
            last_name='User', 
            role='DEVELOPER'
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Investable Project",
            description="Desc",
            category="FinTech",
            duration_days=30,
            total_project_value=Decimal("1000.00"),
            total_shares=100,
            status="APPROVED",
            share_price=Decimal("10.00"),
            shares_sold=0
        )

    def test_initiate_investment_unverified(self):
        self.client.force_authenticate(user=self.unverified_investor)
        url = reverse('investments:investment-initiate')
        data = {
            "project_id": self.project.id,
            "shares_requested": 5,
            "idempotency_key": "unique-key-1"
        }
        response = self.client.post(url, data)
        # Should be 403 Forbidden due to UnverifiedUserError
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initiate_investment_success(self):
        self.client.force_authenticate(user=self.investor)
        url = reverse('investments:investment-initiate')
        data = {
            "project_id": self.project.id,
            "shares_requested": 5,
            "idempotency_key": "unique-key-2"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment_url', response.data['data'])
        self.assertIn('reference_id', response.data['data'])

    def test_idempotency_check(self):
        self.client.force_authenticate(user=self.investor)
        url = reverse('investments:investment-initiate')
        data = {
            "project_id": self.project.id,
            "shares_requested": 5,
            "idempotency_key": "unique-key-3"
        }
        # First request
        self.client.post(url, data)
        
        # Second request with same key
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
