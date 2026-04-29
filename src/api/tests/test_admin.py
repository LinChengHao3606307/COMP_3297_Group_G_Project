from django.test import RequestFactory
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from unittest.mock import MagicMock, patch

from user_home.models import User, Tenant, Domain
from user_home.admin import TenantAdmin, DomainAdmin
# Fix: Import SubclassUserAdmin from api.admin
from api.admin import SubclassUserAdmin 

class AdminLogicTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Ensures the public tenant exists and the test tenant has a valid owner.
        """
        if not Tenant.objects.filter(schema_name='public').exists():
            try:
                create_public_tenant(
                    domain_url="public.testserver", 
                    owner_email="admin_test_root@test.com"
                )
            except ExistsError:
                pass

        with schema_context(get_public_schema_name()):
            owner, created = User.objects.get_or_create(
                email="admin_owner@test.com",
                defaults={"role": User.Role.ADMIN}
            )
            if not owner.check_password("password123"):
                owner.set_password("password123")
                owner.save()

        tenant.owner = owner
        return tenant

    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        
        with schema_context(get_public_schema_name()):
            # Create a test user in the public schema for admin operation tests
            self.test_user, _ = User.objects.get_or_create(
                email="test_staff@test.com",
                defaults={
                    "password": "unhashedpassword123",
                    "role": User.Role.ADMIN
                }
            )

    def test_get_type_method(self):
        """Covers: SubclassUserAdmin.get_type(obj)"""
        admin = SubclassUserAdmin(User, self.site)
        
        # Call get_type using a User instance
        type_name = admin.get_type(self.test_user)
        
        # Verify result is 'user' (the verbose_name of the User model)
        self.assertEqual(type_name.lower(), "user")
        # Verify short_description is set to 'Role'
        self.assertEqual(SubclassUserAdmin.get_type.short_description, 'Role')

    def test_tenant_admin_delete_model_force_drop(self):
        """Covers: TenantAdmin.delete_model(obj)"""
        admin = TenantAdmin(Tenant, self.site)
        mock_tenant = MagicMock(spec=Tenant)
        
        admin.delete_model(None, mock_tenant)
        
        # Check if force_drop=True was passed to the delete method
        mock_tenant.delete.assert_called_once_with(force_drop=True)

    def test_user_admin_password_hashing(self):
        """Covers: BaseUserAdmin.save_model logic via SubclassUserAdmin"""
        admin = SubclassUserAdmin(User, self.site)
        
        # Set a plain text password
        self.test_user.password = "newpassword456"
        
        # Trigger save_model (mimics clicking save in Django Admin)
        admin.save_model(None, self.test_user, None, True)
        
        # Reload and check that it is now a hashed string
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.password.startswith('pbkdf2_'))

    def test_user_admin_prevent_owner_deletion(self):
        """Covers: BaseUserAdmin.delete_model logic (Owner Protection)"""
        admin = SubclassUserAdmin(User, self.site)
        owner = self.tenant.owner 
        
        with self.assertRaises(ValidationError) as cm:
            admin.delete_model(None, owner)
        
        self.assertEqual(cm.exception.message, "You cannot delete a user that is a tenant owner.")

    @patch('user_home.admin.UserProfileManager.delete_user')
    def test_user_admin_delete_via_manager(self, mock_delete_user):
        """Covers: BaseUserAdmin.delete_model logic (UserProfileManager usage)"""
        admin = SubclassUserAdmin(User, self.site)
        
        admin.delete_model(None, self.test_user)
        
        # Verify the custom manager method was called
        mock_delete_user.assert_called_once_with(self.test_user)

    def test_subclass_admin_config(self):
        """Covers: list_display and add_fieldsets configuration in SubclassUserAdmin"""
        admin = SubclassUserAdmin(User, self.site)
        self.assertEqual(admin.list_display, ('id', 'email', 'get_type'))
        self.assertEqual(admin.add_fieldsets[0][1]['fields'], ('email', 'password1', 'password2'))

    def test_domain_admin_list_display(self):
        """Covers: DomainAdmin.list_display"""
        admin = DomainAdmin(Domain, self.site)
        self.assertEqual(list(admin.list_display), ["domain", "tenant", "is_primary"])