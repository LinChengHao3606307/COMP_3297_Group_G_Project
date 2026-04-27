from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name # Add this import
from user_home.models import User
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

class UserModelsTests(TenantTestCase):
    @classmethod
    def setup_tenant(cls, tenant):
        # Fix for ExistsError when using --keepdb
        try:
            create_public_tenant(
                domain_url="public.testserver",
                owner_email="public_admin@test.com"
            )
        except ExistsError:
            pass

        # Fix for SchemaError: Creation must be in public context
        with schema_context(get_public_schema_name()):
            cls.owner, created = User.objects.get_or_create(
                email="admin@test.com",
                defaults={
                    "password": "password123",
                    "role": User.Role.ADMIN
                }
            )
            if not created:
                cls.owner.set_password("password123")
                cls.owner.save()

        tenant.owner = cls.owner
        tenant.name = "Test Tenant"
        return tenant

    def test_creation(self):
        email_dev = "dev@test.com"
        password_dev = "password123"
        
        # Helper function needs the schema context wrapper
        def check_user(email, password, role):
            # Fix for SchemaError here
            with schema_context(get_public_schema_name()):
                user = User.objects.create_user(email=email, password=password, role=role)
                self.assertEqual(user.email, email)
                self.assertTrue(user.check_password(password))
                self.assertEqual(user.role, role)
                return user

        # Now this call will work
        check_user(email_dev, password_dev, User.Role.DEVELOPER)