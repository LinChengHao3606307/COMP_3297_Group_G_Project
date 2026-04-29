from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from rest_framework import status

from user_home.models import User, Tenant
from api.models import Product, Report, Comment

class CommentViewSetTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Ensures the public tenant exists and the test tenant has a valid owner
        assigned before the database attempts to save it.
        """
        # 1. Ensure the Public Tenant exists (shared across all tests)
        if not Tenant.objects.filter(schema_name='public').exists():
            try:
                create_public_tenant(
                    domain_url="public.testserver", 
                    owner_email="public_admin@test.com"
                )
            except ExistsError:
                pass

        # 2. Create/Get a user in the public schema to be the owner
        with schema_context(get_public_schema_name()):
            # Use get_or_create to prevent IntegrityErrors if user exists
            owner, created = User.objects.get_or_create(
                email="comment_admin@test.com",
                defaults={"role": User.Role.ADMIN}
            )
            if not owner.check_password("password123"):
                owner.set_password("password123")
                owner.save()
            
            # Create other necessary users for the test logic
            cls.tester, _ = User.objects.get_or_create(
                email="comment_tester@test.com",
                defaults={"role": User.Role.TESTER}
            )
            cls.tester.set_password("password123")
            cls.tester.save()

            cls.po, _ = User.objects.get_or_create(
                email="comment_po@test.com",
                defaults={"role": User.Role.PRODUCT_OWNER}
            )

        # 3. CRITICAL: Assign the owner to the tenant before returning
        # This prevents the "null value in column owner_id" error
        tenant.owner = owner
        return tenant

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        
        # Add the users to this specific tenant's members
        self.tenant.add_user(self.tester)
        self.tenant.add_user(self.po)

        # Log in as the tester for the comment creation tests
        self.client.force_login(self.tester)

        self.product = Product.objects.create(
            name="TestProduct",
            version="1.0",
            owner=self.po
        )

        self.report = Report.objects.create(
            product=self.product,
            title="UI Bug",
            description="Button alignment is off",
            steps_to_reproduce="Open home page",
            email="comment_tester@test.com",
            status=Report.Status.NEW
        )

        self.comment_data = {"content": "Verified the bug."}

    def test_tester_can_create_comment(self):
        # Correct URL (no /api/ prefix as per your urls.py)
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], self.comment_data['content'])
        self.assertEqual(response.data['author']['email'], self.tester.email)

    def test_unauthenticated_user_cannot_create_comment(self):
        self.client.logout()
        url = f"/products/{self.product.id}/report/{self.report.id}/comments/"
        response = self.client.post(url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)