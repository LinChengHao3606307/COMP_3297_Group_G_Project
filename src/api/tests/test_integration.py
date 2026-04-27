from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

from ..models import *

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
        cls.tester = User.objects.create_user(email="tester@localhost", password="asd", role=User.Role.TESTER)
        cls.dev = User.objects.create_user(email="dev@loaclhost", password="", role=User.Role.DEVELOPER)
        # 3. Setup the specific test tenant
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

    def test_base_link(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("products", r.data)
        self.assertIn("users", r.data)

    def test_create_user(self):
        email_dev = "uin89y34iomdvsm@a.com"
        password_dev = "sdfvioh24qt89ynjkf"
        email_po = "nuojdvs89023riondvsion235.sdv@b.com"
        password_po = "asd89yu3r2iond23bgwtrenyyu"

        def test(email, password, role):
            r = self.client.post("/users/register", {"email": email, "password": password, "role": role})
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)
            self.assertHasAttr(r, "data")
            self.assertIn("id", r.data)
            self.assertEqual(r.data["email"], email)

            self.assertEqual(User.objects.filter(role=role).count(), 1)
            user = User.objects.filter(role=role)[0]
            self.assertEqual(user.email, email)
            self.assertEqual(user.role, role)
            self.assertTrue(user.check_password(password))

        test(email_dev, password_dev, User.Role.DEVELOPER)
        test(email_po, password_po, User.Role.PRODUCT_OWNER)

    def test_full_cycle(self):
        # PO: Create product
        self.client.force_login(user=self.owner)
        name = "Test Product"
        version = "1.0.0"
        r = self.client.post("/products/", data={"name": name, "version": version})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.all()[0]
        self.assertEqual(product.name, name)
        self.assertEqual(product.version, version)

        # Tester: Look for the products
        self.client.force_login(user=self.tester)
        r = self.client.get("/products/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertIn("reports", r.data[0])
        report_endpoint = r.data[0]["reports"]
        print(report_endpoint)

        # Create report
        title = "Test Report"
        description = "Test"
        steps = "Test 2"
        email = "t@b.com"
        r = self.client.post("/")
        # not done yet

