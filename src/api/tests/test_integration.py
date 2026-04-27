from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from user_home.models import User, Tenant
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

class IntegrationTests(TenantTestCase):
    
    @classmethod
    def setup_tenant(cls, tenant):
        # 1. Safely bootstrap the public tenant, domain, and a public owner
        try:
            create_public_tenant(
                domain_url="public.testserver",
                owner_email="public_admin@test.com"
            )
        except ExistsError:
            pass

        # 2. Now you can safely create your test tenant's owner
        cls.owner = User.objects.create_user(
            email="super@test.com", 
            password="password123", 
            role=User.Role.PRODUCT_OWNER
        )

        # 3. Setup the specific test tenant
        tenant.owner = cls.owner
        tenant.name = "Test Tenant"
        return tenant

    def setUp(self):
        super().setUp()
        self.tenant.add_user(self.owner, is_superuser=True)

        self.client = TenantClient(self.tenant)
        self.client.force_login(user=self.owner)

    def test_base_link(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("products", r.data)
        self.assertIn("users", r.data)