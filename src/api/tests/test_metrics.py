# src/api/tests/test_metrics.py
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from user_home.models import User


class MetricsCoverageTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(
                domain_url="public.testserver", 
                owner_email="admin@test.com"
            )
        except ExistsError:
            pass

        with schema_context(get_public_schema_name()):
            cls.admin_user, _ = User.objects.get_or_create(
                email="admin_metrics@test.com",
                defaults={"role": User.Role.ADMIN}
            )
            if not cls.admin_user.check_password("password123"):
                cls.admin_user.set_password("password123")
                cls.admin_user.save()

        tenant.owner = cls.admin_user
        return tenant

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)
        self.client.force_login(self.admin_user)

    def test_developer_effectiveness(self):
        """Test developer metrics endpoint - Robust version"""
        # Create developer
        with schema_context(get_public_schema_name()):
            dev, _ = User.objects.get_or_create(
                email="dev_metrics@test.com",
                defaults={"role": User.Role.DEVELOPER}
            )
            if not dev.check_password("pw"):
                dev.set_password("pw")
                dev.save()

        self.tenant.add_user(dev)

        dev.fixed_report = 25
        dev.reopened_report = 2
        dev.save()

        url = f"/developer-metrics/{dev.id}/"

        # === Most reliable way for tenant tests ===
        with schema_context(self.tenant.schema_name):
            # Set the correct host so TenantMainMiddleware can identify the tenant
            response = self.client.get(
                url, 
                HTTP_HOST=f"{self.tenant.schema_name}.localhost"
            )

        self.assertEqual(
            response.status_code, 
            200, 
            f"Expected 200 but got {response.status_code}. "
            f"URL: {url} | Tenant: {self.tenant.schema_name} | Host: {self.tenant.schema_name}.localhost"
        )
        
        data = response.data
        self.assertIn('effectiveness', data)
        self.assertEqual(data['fixed_report'], 25)
        self.assertEqual(data['reopened_report'], 2)
        self.assertIn(data['effectiveness'], ["Good", "Fair", "Poor", "Insufficient data"])
        self.assertAlmostEqual(data.get('reopened_ratio'), 0.08, places=4)