from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project
from decimal import Decimal
import uuid

User = get_user_model()

class ProjectTests(APITestCase):
    def setUp(self):
        # Create Users with different roles
        self.developer = User.objects.create_user(
            email=f'dev_{uuid.uuid4()}@example.com', 
            password='password123', 
            first_name='Dev',
            last_name='User',
            role='DEVELOPER', 
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
        self.admin = User.objects.create_user(
            email=f'admin_{uuid.uuid4()}@example.com', 
            password='password123', 
            first_name='Admin',
            last_name='User',
            role='ADMIN', 
            is_superuser=True, 
            is_active=True,
            is_email_verified=True
        )

        # Create Initial Projects
        self.project_draft = Project.objects.create(
            developer=self.developer,
            title="Draft Project",
            description="Description Draft",
            category="Tech",
            duration_days=30,
            total_project_value=Decimal("10000.00"),
            total_shares=100,
            status="DRAFT"
        )
        self.project_approved = Project.objects.create(
            developer=self.developer,
            title="Approved Project",
            description="Description Approved",
            category="Real Estate",
            duration_days=60,
            total_project_value=Decimal("50000.00"),
            total_shares=1000,
            status="APPROVED",
            share_price=Decimal("50.00"),
            shares_sold=0
        )

    def test_project_create_and_permissions(self):
        # Unauthenticated try
        url = reverse('project-list-create')
        data = {
            "title": "New Project",
            "description": "Desc",
            "category": "Energy",
            "duration_days": 45,
            "total_project_value": "20000.00",
            "total_shares": 200
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Investor try (Should Fail - 403)
        self.client.force_authenticate(user=self.investor)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Developer try (Should Success)
        self.client.force_authenticate(user=self.developer)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(Project.objects.latest('created_at').status, 'DRAFT')

    def test_project_browsing_list(self):
        # Browse via GET /api/v1/projects/ (Fix 405 check)
        self.client.force_authenticate(user=self.investor)
        url = reverse('project-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check standard envelope { data: { results: [...] } }
        self.assertIn('data', response.data)
        self.assertIn('results', response.data['data'])
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['id'], str(self.project_approved.id))

        # Browse via GET /api/v1/projects/browse/ (Explicit OAS path)
        url_browse = reverse('investor-browse-projects')
        response = self.client.get(url_browse)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_project_detail(self):
        self.client.force_authenticate(user=self.investor)
        url = reverse('project-detail', args=[self.project_approved.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], self.project_approved.title)

    def test_developer_my_projects(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('my-projects')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see both draft and approved
        self.assertEqual(len(response.data['data']['results']), 2)

    def test_project_workflow_submit_approve(self):
        # 1. Submit (Developer)
        self.client.force_authenticate(user=self.developer)
        url_submit = reverse('project-submit', args=[self.project_draft.id])
        response = self.client.post(url_submit)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_draft.refresh_from_db()
        self.assertEqual(self.project_draft.status, 'PENDING')

        # 2. Check Pending List (Admin)
        self.client.force_authenticate(user=self.admin)
        url_pending = reverse('admin-pending-projects')
        response = self.client.get(url_pending)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)
        self.assertEqual(response.data['data']['results'][0]['id'], str(self.project_draft.id))

        # 3. Approve (Admin)
        url_approve = reverse('admin-approve-project', args=[self.project_draft.id])
        response = self.client.post(url_approve)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project_draft.refresh_from_db()
        self.assertEqual(self.project_draft.status, 'APPROVED')

    def test_compare_projects(self):
        # Need at least 2 approved projects
        project_2 = Project.objects.create(
            developer=self.developer,
            title="Approved 2",
            description="Desc",
            category="Tech",
            duration_days=30,
            total_project_value=Decimal("10.00"),
            total_shares=10,
            status="APPROVED",
            share_price=Decimal("1.00"),
            shares_sold=0
        )
        
        self.client.force_authenticate(user=self.investor)
        ids = f"{self.project_approved.id},{project_2.id}"
        url = reverse('investor-compare-projects') + f"?ids={ids}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check standard envelope format
        self.assertEqual(response.data['data']['count'], 2)

    def test_restricted_fields_visibility(self):
        # Setup project with restricted fields
        self.project_approved.restricted_fields = ["secret_doc_url"]
        self.project_approved.save()
        
        # 1. Developer (Owner) should see it
        self.client.force_authenticate(user=self.developer)
        url = reverse('project-detail', args=[self.project_approved.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: Developer sees data, but serializer filters restricted_fields? 
        # Check serializer logic: if user == developer, has_access=True.
        # So restricted_fields should be present.
        
        # 2. Investor (No Access) should NOT see it
        self.client.force_authenticate(user=self.investor)
        url = reverse('project-detail', args=[self.project_approved.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('restricted_fields', response.data['data'])
        
        # 3. Admin should see it
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('restricted_fields', response.data['data'])
        self.assertEqual(response.data['data']['restricted_fields'], ["secret_doc_url"])
