from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from .models import AccessRequest
from decimal import Decimal
import uuid

User = get_user_model()

class AccessRequestAdminTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email=f'admin_{uuid.uuid4()}@example.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_email_verified=True
        )
        self.investor = User.objects.create_user(
            email=f'inv_{uuid.uuid4()}@example.com',
            password='password123',
            first_name='Inv',
            last_name='User',
            role='INVESTOR',
            is_active=True,
            is_email_verified=True
        )
        self.developer = User.objects.create_user(
            email=f'dev_{uuid.uuid4()}@example.com',
            password='password123',
            first_name='Dev',
            last_name='User',
            role='DEVELOPER',
            is_active=True,
            is_email_verified=True
        )

        self.project = Project.objects.create(
            developer=self.developer,
            title="Skyline Apartments",
            description="Description",
            category="Real Estate",
            duration_days=60,
            total_project_value=Decimal("50000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("50.00")
        )

        self.access_request = AccessRequest.objects.create(
            project=self.project,
            investor=self.investor,
            reason="I want to see financial details",
            status="PENDING"
        )

        self.url = reverse('access-request-admin-list')

    def test_admin_can_list_all_requests(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check standard envelope { data: { results: [...] } }
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['requester_email'], self.investor.email)
        self.assertEqual(response.data['data']['results'][0]['project_title'], self.project.title)

    def test_non_admin_cannot_access(self):
        self.client.force_authenticate(user=self.investor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.admin)
        
        # Create an approved request
        project2 = Project.objects.create(
            developer=self.developer,
            title="Project 2",
            description="Description",
            category="Energy",
            duration_days=30,
            total_project_value=Decimal("10000.00"),
            total_shares=100,
            status="APPROVED"
        )
        AccessRequest.objects.create(
            project=project2,
            investor=self.investor,
            reason="Another reason",
            status="APPROVED"
        )

        # Filter by PENDING
        response = self.client.get(self.url + "?status=PENDING")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'PENDING')

        # Filter by APPROVED
        response = self.client.get(self.url + "?status=APPROVED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'APPROVED')

    def test_search_functionality(self):
        self.client.force_authenticate(user=self.admin)
        
        # Search by project title
        response = self.client.get(self.url + "?search=Skyline")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['project_title'], "Skyline Apartments")

        # Search by investor email
        response = self.client.get(self.url + f"?search={self.investor.email}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['requester_email'], self.investor.email)
