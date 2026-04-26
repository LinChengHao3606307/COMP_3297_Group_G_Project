from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from tenant_users.tenants.utils import create_public_tenant
from user_home.models import Tenant

User = get_user_model()


class UserModelsTests(TransactionTestCase):
    def setUp(self):
        # 確保清理舊資料，避免重複建立
        Tenant.objects.all().delete()
        User.objects.all().delete()

        # 修正參數名稱為 domain_url
        self.tenant = create_public_tenant(
            domain_url='localhost',
            owner_email='admin@test.com',
        )

    def test_creation(self):
        email_dev = "dev@example.com"
        password_dev = "password123"
        role = User.Role.DEVELOPER

        user = User.objects.create_user(
            email=email_dev,
            password=password_dev,
            role=role
        )

        self.assertEqual(user.email, email_dev)
        self.assertTrue(user.check_password(password_dev))
