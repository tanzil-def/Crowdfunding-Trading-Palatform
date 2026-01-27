from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.investments.models import PaymentTransaction, SharePurchase
from decimal import Decimal
import uuid
import hmac
import hashlib
import json

User = get_user_model()

class InvestmentInitiateTests(APITestCase):
    """Test suite for investment initiation endpoint"""
    
    def setUp(self):
        """Create test users and projects"""
        self.investor = User.objects.create_user(
            email='investor@example.com',
            password='password123',
            first_name='John',
            last_name='Investor',
            role='INVESTOR',
            is_active=True,
            is_email_verified=True
        )
        
        self.unverified_investor = User.objects.create_user(
            email='unverified@example.com',
            password='password123',
            first_name='Jane',
            last_name='Unverified',
            role='INVESTOR',
            is_active=True,
            is_email_verified=False
        )
        
        self.developer = User.objects.create_user(
            email='developer@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER',
            is_active=True,
            is_email_verified=True
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Investable Project",
            description="A project for testing investments",
            category="Real Estate",
            duration_days=30,
            total_project_value=Decimal("100000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("100.00"),
            shares_sold=0
        )
        
        self.pending_project = Project.objects.create(
            developer=self.developer,
            title="Pending Project",
            description="Not approved yet",
            category="FinTech",
            duration_days=30,
            total_project_value=Decimal("50000.00"),
            total_shares=500,
            status="PENDING_REVIEW",
            share_price=Decimal("100.00"),
            shares_sold=0
        )

    def test_initiate_investment_success(self):
        """Test successful investment initiation"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:investment-initiate')
        data = {
            'project_id': str(self.project.id),
            'shares_requested': 10,
            'idempotency_key': str(uuid.uuid4())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.json())
        self.assertIn('reference_id', response.json()['data'])
        self.assertIn('payment_url', response.json()['data'])

    def test_initiate_investment_unverified_investor(self):
        """Test that unverified investors cannot initiate investment"""
        self.client.force_authenticate(user=self.unverified_investor)
        
        url = reverse('investments:investment-initiate')
        data = {
            'project_id': str(self.project.id),
            'shares_requested': 10,
            'idempotency_key': str(uuid.uuid4())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initiate_investment_pending_project(self):
        """Test that pending projects cannot receive investments"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:investment-initiate')
        data = {
            'project_id': str(self.pending_project.id),
            'shares_requested': 10,
            'idempotency_key': str(uuid.uuid4())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_initiate_investment_insufficient_shares(self):
        """Test that request fails when insufficient shares available"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:investment-initiate')
        data = {
            'project_id': str(self.project.id),
            'shares_requested': 2000,  # More than available
            'idempotency_key': str(uuid.uuid4())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_initiate_investment_idempotency(self):
        """Test that duplicate idempotency_key returns error"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:investment-initiate')
        idempotency_key = str(uuid.uuid4())
        data = {
            'project_id': str(self.project.id),
            'shares_requested': 10,
            'idempotency_key': idempotency_key
        }
        
        # First request succeeds
        response1 = self.client.post(url, data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second request with same idempotency_key should fail
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)

    def test_initiate_investment_not_authenticated(self):
        """Test that unauthenticated users cannot initiate investment"""
        url = reverse('investments:investment-initiate')
        data = {
            'project_id': str(self.project.id),
            'shares_requested': 10,
            'idempotency_key': str(uuid.uuid4())
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PaymentTransactionModelTests(APITestCase):
    """Test suite for PaymentTransaction model"""
    
    def setUp(self):
        """Create test data"""
        self.investor = User.objects.create_user(
            email='investor@example.com',
            password='password123',
            first_name='John',
            last_name='Investor',
            role='INVESTOR',
            is_active=True,
            is_email_verified=True
        )
        
        self.developer = User.objects.create_user(
            email='developer@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER'
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Test Project",
            description="Test",
            category="Real Estate",
            duration_days=30,
            total_project_value=Decimal("100000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("100.00"),
            shares_sold=0
        )

    def test_create_payment_transaction(self):
        """Test creating a payment transaction"""
        payment = PaymentTransaction.objects.create(
            reference_id='TXN-001',
            idempotency_key='KEY-001',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_INITIATED
        )
        
        self.assertEqual(payment.reference_id, 'TXN-001')
        self.assertEqual(payment.status, PaymentTransaction.STATUS_INITIATED)
        self.assertEqual(payment.amount, Decimal('1000.00'))
        self.assertEqual(payment.price_per_share, Decimal('100.00'))

    def test_payment_transaction_is_completed(self):
        """Test is_completed method"""
        initiated = PaymentTransaction.objects.create(
            reference_id='TXN-002',
            idempotency_key='KEY-002',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_INITIATED
        )
        
        success = PaymentTransaction.objects.create(
            reference_id='TXN-003',
            idempotency_key='KEY-003',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_SUCCESS
        )
        
        self.assertFalse(initiated.is_completed())
        self.assertTrue(success.is_completed())

    def test_idempotency_key_uniqueness(self):
        """Test that idempotency_key must be unique"""
        PaymentTransaction.objects.create(
            reference_id='TXN-004',
            idempotency_key='KEY-004',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_INITIATED
        )
        
        with self.assertRaises(Exception):
            PaymentTransaction.objects.create(
                reference_id='TXN-005',
                idempotency_key='KEY-004',  # Duplicate key
                investor=self.investor,
                project=self.project,
                amount=Decimal('1000.00'),
                shares_requested=10,
                status=PaymentTransaction.STATUS_INITIATED
            )


class SharePurchaseTests(APITestCase):
    """Test suite for SharePurchase model"""
    
    def setUp(self):
        """Create test data"""
        self.investor = User.objects.create_user(
            email='investor@example.com',
            password='password123',
            first_name='John',
            last_name='Investor',
            role='INVESTOR'
        )
        
        self.developer = User.objects.create_user(
            email='developer@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER'
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Test Project",
            description="Test",
            category="Real Estate",
            duration_days=30,
            total_project_value=Decimal("100000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("100.00"),
            shares_sold=0
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference_id='TXN-001',
            idempotency_key='KEY-001',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_SUCCESS
        )

    def test_create_share_purchase(self):
        """Test creating a share purchase"""
        purchase = SharePurchase.objects.create(
            investor=self.investor,
            project=self.project,
            payment_transaction=self.payment,
            shares_purchased=10,
            price_per_share=Decimal('100.00'),
            total_amount=Decimal('1000.00')
        )
        
        self.assertEqual(purchase.shares_purchased, 10)
        self.assertEqual(purchase.total_amount, Decimal('1000.00'))

    def test_share_purchase_consistency(self):
        """Test that share purchase validates amount consistency"""
        purchase = SharePurchase.objects.create(
            investor=self.investor,
            project=self.project,
            payment_transaction=self.payment,
            shares_purchased=10,
            price_per_share=Decimal('100.00'),
            total_amount=Decimal('1000.00')
        )
        
        # validate_consistency should pass
        try:
            purchase.validate_consistency()
        except Exception as e:
            self.fail(f"validate_consistency raised {e}")

    def test_share_purchase_auto_total_amount(self):
        """Test that total_amount is calculated automatically"""
        purchase = SharePurchase.objects.create(
            investor=self.investor,
            project=self.project,
            payment_transaction=self.payment,
            shares_purchased=10,
            price_per_share=Decimal('100.00')
        )
        
        self.assertEqual(purchase.total_amount, Decimal('1000.00'))


class InvestmentListTests(APITestCase):
    """Test suite for investment listing endpoint"""
    
    def setUp(self):
        """Create test data"""
        self.investor = User.objects.create_user(
            email='investor@example.com',
            password='password123',
            first_name='John',
            last_name='Investor',
            role='INVESTOR',
            is_email_verified=True
        )
        
        self.developer = User.objects.create_user(
            email='developer@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER'
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Test Project",
            description="Test",
            category="Real Estate",
            duration_days=30,
            total_project_value=Decimal("100000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("100.00"),
            shares_sold=10
        )
        
        # Create a successful payment and share purchase
        self.payment = PaymentTransaction.objects.create(
            reference_id='TXN-001',
            idempotency_key='KEY-001',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_SUCCESS
        )
        
        self.purchase = SharePurchase.objects.create(
            investor=self.investor,
            project=self.project,
            payment_transaction=self.payment,
            shares_purchased=10,
            price_per_share=Decimal('100.00'),
            total_amount=Decimal('1000.00')
        )

    def test_list_my_investments(self):
        """Test listing investor's investments"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:my-investments')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 1)
        self.assertEqual(response.json()['results'][0]['shares_purchased'], 10)

    def test_portfolio_summary(self):
        """Test portfolio summary endpoint"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:portfolio-summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['data']
        self.assertEqual(data['total_invested'], '1000.00')
        self.assertEqual(data['projects_invested'], 1)
        self.assertEqual(data['total_shares_owned'], 10)
        self.assertEqual(data['investment_count'], 1)


class AdminTransactionTests(APITestCase):
    """Test suite for admin transaction endpoints"""
    
    def setUp(self):
        """Create test data"""
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        
        self.investor = User.objects.create_user(
            email='investor@example.com',
            password='password123',
            first_name='John',
            last_name='Investor',
            role='INVESTOR',
            is_email_verified=True
        )
        
        self.developer = User.objects.create_user(
            email='developer@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER'
        )
        
        self.project = Project.objects.create(
            developer=self.developer,
            title="Test Project",
            description="Test",
            category="Real Estate",
            duration_days=30,
            total_project_value=Decimal("100000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("100.00"),
            shares_sold=0
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference_id='TXN-001',
            idempotency_key='KEY-001',
            investor=self.investor,
            project=self.project,
            amount=Decimal('1000.00'),
            shares_requested=10,
            status=PaymentTransaction.STATUS_SUCCESS
        )

    def test_admin_transactions_list(self):
        """Test admin can list all transactions"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('investments:admin-transactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()['data']['results']), 1)

    def test_admin_transaction_detail(self):
        """Test admin can view transaction details"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('investments:admin-transaction-detail', kwargs={'id': self.payment.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['reference_id'], 'TXN-001')

    def test_non_admin_cannot_view_transactions(self):
        """Test that non-admin users cannot view admin transactions"""
        self.client.force_authenticate(user=self.investor)
        
        url = reverse('investments:admin-transactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
