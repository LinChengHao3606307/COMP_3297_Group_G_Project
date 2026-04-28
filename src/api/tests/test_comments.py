from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from rest_framework import status

from user_home.models import User
from api.models import Product, Report, Comment


class CommentViewSetTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        """Setup public tenant and test users safely"""
        # Create public tenant if it doesn't exist
        try:
            create_public_tenant(
                domain_url="public.testserver", 
                owner_email="admin@test.com"
            )
        except ExistsError:
            pass

        # Create users safely in public schema
        with schema_context(get_public_schema_name()):
            users_data = [
                ("po@test.com", User.Role.PRODUCT_OWNER),
                ("dev@test.com", User.Role.DEVELOPER),
                ("tester@test.com", User.Role.TESTER),
                ("admin@test.com", User.Role.ADMIN),
            ]

            for email, role in users_data:
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={"role": role}
                )
                if created or not user.check_password("password123"):
                    user.set_password("password123")
                    user.save()

            # Assign to class attributes for easy access in tests
            cls.po = User.objects.get(email="po@test.com")
            cls.dev = User.objects.get(email="dev@test.com")
            cls.tester = User.objects.get(email="tester@test.com")
            cls.admin = User.objects.get(email="admin@test.com")

        tenant.owner = cls.po
        return tenant

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

        # Add all users to the current tenant (safe to call multiple times)
        for user in [self.po, self.dev, self.tester, self.admin]:
            self.tenant.add_user(user)

        # Default login as tester (most common use case for comments)
        self.client.force_login(self.tester)

        # Create common test data: Product + Report
        self.product = Product.objects.create(
            name="TestProduct",
            version="1.0",
            owner=self.po
        )

        self.report = Report.objects.create(
            product=self.product,
            title="Login Button Broken",
            description="The login button does nothing when clicked",
            steps_to_reproduce="1. Go to login page\n2. Click login button",
            email="tester@test.com",
            status=Report.Status.NEW
        )

        self.comment_data = {
            "content": "I can reproduce this issue on Chrome."
        }

    # ====================== SUCCESS CASES ======================

    def test_tester_can_create_comment(self):
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], self.comment_data['content'])
        self.assertEqual(response.data['author']['email'], self.tester.email)

        self.assertEqual(Comment.objects.count(), 1)

    def test_developer_can_create_comment(self):
        self.client.force_login(self.dev)
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_owner_can_create_comment(self):
        self.client.force_login(self.po)
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_create_comment(self):
        self.client.force_login(self.admin)
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ====================== FAILURE CASES ======================

    def test_unauthenticated_user_cannot_create_comment(self):
        self.client.logout()
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_comment_on_nonexistent_report(self):
        self.client.force_login(self.tester)
        url = f"/products/{self.product.id}/report/99999/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ====================== READ PERMISSIONS ======================

    def test_anyone_can_list_comments(self):
        # Create a sample comment
        Comment.objects.create(
            report=self.report,
            author=self.tester,
            content="Existing comment"
        )

        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_anyone_can_retrieve_single_comment(self):
        comment = Comment.objects.create(
            report=self.report,
            author=self.dev,
            content="Test comment for retrieval"
        )

        url = f"/products/{self.product.id}/report/{self.report.id}/comments/{comment.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], "Test comment for retrieval")