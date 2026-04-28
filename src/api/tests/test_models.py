from itertools import product

from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name
from django_tenants.test.client import TenantClient

from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

from ..models import *

class ModelsTests(TenantTestCase):
    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(domain_url="public.testserver", owner_email="public_admin@test.com")
        except ExistsError:
            pass

        cls.owner = User.objects.create_user(email="po@ModelsTests", password="password123", role=User.Role.PRODUCT_OWNER)
        cls.tester = User.objects.create_user(email="tester@ModelsTests", password="asd", role=User.Role.TESTER)
        cls.dev = User.objects.create_user(email="dev@ModelsTests", password="", role=User.Role.DEVELOPER)

        tenant.owner = cls.owner
        tenant.name = "Test Tenant"
        return tenant

    def setUp(self):
        super().setUp()
        self.tenant.add_user(self.owner, is_superuser=True)
        self.tenant.add_user(self.tester)
        self.tenant.add_user(self.dev)
        self.client = TenantClient(self.tenant)
        self.client.force_login(user=self.owner)

    def test_create_user(self):
        email_dev = "dev@test.com"
        password_dev = "password123"
    
        def check_user(email, password, role):
            with schema_context(get_public_schema_name()):
                # Use get_or_create + set password safely
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={"role": role}
                )
                if not user.check_password(password):
                    user.set_password(password)
                    user.save()
                
                self.assertEqual(user.email, email)
                self.assertTrue(user.check_password(password))
                self.assertEqual(user.role, role)
                return user

        check_user(email_dev, password_dev, User.Role.DEVELOPER)

    def test_create_product(self):
        name = "Test Product"
        version = "1.0"
        product = Product.objects.create(name=name, version=version, owner=self.owner)
        self.assertEqual(product.name, name)
        self.assertEqual(product.version, version)
        self.assertEqual(product.owner, self.owner)
        self.assertEqual(str(product), f"Product '{name} v{version}' ({self.owner})")

    def test_create_report(self):
        title = "Test Report"
        description = "Test Description"
        steps = "Test Steps"
        email = "Test Email"
        product = Product.objects.create(name="a", version="a", owner=self.owner)
        report = Report.objects.create(title=title, description=description, steps_to_reproduce=steps, email=email, product=product)
        self.assertEqual(report.title, title)
        self.assertEqual(report.description, description)
        self.assertEqual(report.steps_to_reproduce, steps)
        self.assertEqual(report.email, email)
        self.assertEqual(report.product, product)
        self.assertEqual(str(report), f"Report '{title}' ({product})")

    def test_create_comment(self):
        product = Product.objects.create(name="a", version="a", owner=self.owner)
        report = Report.objects.create(title="a", description="a", steps_to_reproduce="a", email="a", product=product)
        content = "Test Comment"
        comment = Comment.objects.create(report=report, content=content, author=self.dev)
        self.assertEqual(comment.content, content)
        self.assertEqual(comment.author, self.dev)
        self.assertEqual(str(comment), f"Comment #{comment.id} ({self.dev} at {comment.created_at} on {report})" )