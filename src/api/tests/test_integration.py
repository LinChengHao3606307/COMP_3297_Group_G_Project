from coverage import report
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

from ..models import *

class BlankTests(TenantTestCase):
    # Tests where only the users exist at first
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
            email="po@BlankTests",
            password="password123", 
            role=User.Role.PRODUCT_OWNER
        )
        cls.tester = User.objects.create_user(email="tester@BlankTests", password="asd", role=User.Role.TESTER)
        cls.dev = User.objects.create_user(email="dev@BlankTests", password="", role=User.Role.DEVELOPER)

        # 3. Set up the specific test tenant
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

    def test_schema_view(self):
        r = self.client.get("/api/schema/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create_user(self):
        email_dev = "uin89y34iomdvsm@a.com"
        password_dev = "sdfvioh24qt89ynjkf"
        email_po = "nuojdvs89023riondvsion235.sdv@b.com"
        password_po = "asd89yu3r2iond23bgwtrenyyu"

        def test(email, password, role):
            r = self.client.post("/users/", {"email": email, "password": password, "role": role})
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)
            self.assertHasAttr(r, "data")
            self.assertEqual(r.data["email"], email)
            self.assertEqual(r.data["role"], role)

            self.assertEqual(User.objects.filter(email=email).count(), 1)
            user = User.objects.filter(email=email)[0]
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
        self.assertHasAttr(r, "data")
        self.assertIn("id", r.data)
        product_id = r.data["id"]
        product = Product.objects.get(id=product_id)
        self.assertEqual(product.name, name)
        self.assertEqual(product.version, version)

        # Tester: Look for the products
        self.client.force_login(user=self.tester)
        r = self.client.get("/products/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)
        self.assertIn("reports", r.data[0])

        # Tester: Create report
        self.client.force_login(user=self.tester)
        title = "Test Report"
        description = "Test"
        steps = "Test 2"
        email = "t@b.com"
        r = self.client.post(f"/products/{product_id}/report/", data={"title": title, "description": description, "steps_to_reproduce": steps, "email": email})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["title"], title)
        self.assertEqual(r.data["description"], description)
        self.assertEqual(r.data["steps_to_reproduce"], steps)
        self.assertEqual(r.data["email"], email)
        self.assertIn("id", r.data)
        report_id = r.data["id"]
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.title, title)
        self.assertEqual(report.description, description)
        self.assertEqual(report.steps_to_reproduce, steps)
        self.assertEqual(report.email, email)
        self.assertEqual(report.priority, "")
        self.assertEqual(report.severity, "")
        self.assertEqual(report.status, Report.Status.NEW)

        # PO: Get report
        self.client.force_login(user=self.owner)
        r = self.client.get(f"/products/{product_id}/report/{report_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], "New")
        self.assertEqual(r.data["comment_count"], 0)

        # PO: Evaluate report to Open
        self.client.force_login(user=self.owner)
        severity = Report.Severity.CRITICAL
        priority = Report.Priority.CRITICAL
        r = self.client.put(f"/products/{product_id}/report/{report_id}/", data={"status": Report.Status.OPEN, "severity": severity, "priority": priority}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, Report.Status.OPEN)
        self.assertEqual(report.priority, priority)
        self.assertEqual(report.severity, severity)

        # Dev: Assign report to self
        self.client.force_login(user=self.dev)
        r = self.client.get(f"/products/{product_id}/report/{report_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Report.Status.OPEN)
        self.assertEqual(r.data["severity"], severity)
        self.assertEqual(r.data["priority"], priority)
        r = self.client.put(f"/products/{product_id}/report/{report_id}/", data={"status": Report.Status.ASSIGNED}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, Report.Status.ASSIGNED)
        self.assertEqual(report.assigned_to, self.dev)

        # Dev: Claim report as fixed
        self.client.force_login(user=self.dev)
        r = self.client.get(f"/products/{product_id}/report/{report_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Report.Status.ASSIGNED)
        self.assertEqual(r.data["assigned_to"]["email"], self.dev.email)
        r = self.client.put(f"/products/{product_id}/report/{report_id}/", data={"status": Report.Status.FIXED}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, Report.Status.FIXED)

        # PO: Resolve the report
        self.client.force_login(user=self.owner)
        r = self.client.get(f"/products/{product_id}/report/{report_id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], Report.Status.FIXED)
        r = self.client.put(f"/products/{product_id}/report/{report_id}/", data={"status": Report.Status.RESOLVED}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        report = Report.objects.get(id=report_id)
        self.assertEqual(report.status, Report.Status.RESOLVED)

        
class ReportTests(TenantTestCase):
    # Tests where users of different roles, and one product and one report are created
    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(domain_url="public.testserver", owner_email="public_admin@test.com")
        except ExistsError:
            pass

        cls.owner = User.objects.create_user(email="pO@ReportTests", password="password123", role=User.Role.PRODUCT_OWNER)
        cls.tester = User.objects.create_user(email="tester@ReportTests", password="asd", role=User.Role.TESTER)
        cls.dev = User.objects.create_user(email="dev@ReportTests", password="", role=User.Role.DEVELOPER)

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
        self.product = Product.objects.create(name="Test Product", version="1.0", owner=self.owner)
        self.report = Report.objects.create(title="a", description="a", steps_to_reproduce="a", email="a", product=self.product)

    def test_duplicate_mark(self):
        self.client.force_login(user=self.owner)
        self.report.status = Report.Status.OPEN
        self.report.save()
        report2 = Report.objects.create(title="a", description="a", steps_to_reproduce="a", email="a", product=self.product)
        r = self.client.put(f"/products/{self.product.id}/report/{report2.id}/", {"status": Report.Status.DUPLICATE, "duplicated_to": self.report.id}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        report2 = Report.objects.get(id=report2.id)
        self.assertEqual(report2.status, Report.Status.DUPLICATE)
        self.assertEqual(report2.duplicated_to, self.report)

        r = self.client.get(f"/products/{self.product.id}/report/{report2.id}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("duplicated_to", r.data)

    def test_duplicate_mark_fail(self):
        self.client.force_login(user=self.owner)
        report2 = Report.objects.create(title="a", description="a", steps_to_reproduce="a", email="a", product=self.product)
        r = self.client.put(f"/products/{self.product.id}/report/{report2.id}/", {"status": Report.Status.DUPLICATE, "duplicated_to": self.report.id}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", r.data)  # "A report cannot be marked as duplicate of itself."

        self.report.status = Report.Status.OPEN
        self.report.save()

        r = self.client.put(f"/products/{self.product.id}/report/{report2.id}/", {"status": Report.Status.DUPLICATE}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", r.data)  # "This field is required when changing status to DUPLICATE."

        r = self.client.put(f"/products/{self.product.id}/report/{report2.id}/", {"status": Report.Status.DUPLICATE, "duplicated_to": report2.id},
                            content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", r.data)  # "A report cannot be marked as duplicate of itself."

    def test_garbage_status(self):
        self.client.force_login(user=self.owner)
        r = self.client.put(f"/products/{self.product.id}/report/{self.report.id}/", {"status": "GETFIXEDBOI"}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", r.data)  # f"'{status_input}' is not a valid choice. Available options: {', '.join(valid_choices)}"

        r = self.client.put(f"/products/{self.product.id}/report/{self.report.id}/", {"status": "OPEN"}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", r.data)  # "Priority and severity must be set when report is NEW"

    def test_developer_metrics(self):
        self.client.force_login(user=self.dev)
        r = self.client.get(f"/developer-metrics/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.dev.fixed_report = 1
        self.dev.save()
        r = self.client.get(f"/developer-metrics/")
        self.dev.fixed_report = 100
        self.dev.reopened_report = 50
        self.dev.save()
        r = self.client.get(f"/developer-metrics/")
        self.dev.reopened_report = 10
        self.dev.save()
        r = self.client.get(f"/developer-metrics/")
        self.dev.reopened_report = 1
        self.dev.save()
        r = self.client.get(f"/developer-metrics/")

    def test_modify_report(self):
        self.client.force_login(user=self.owner)
        r = self.client.put(f"/products/{self.product.id}/", {"name": "aaa", "version": "2.0"}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["version"], "2.0")


class AdminPermissionTests(TenantTestCase):
    # Tests permissions for admin
    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(domain_url="public.testserver", owner_email="public_admin@test.com")
        except ExistsError:
            pass

        cls.owner = User.objects.create_user(email="admin@AdminPermissionTests", password="password123",
                                             role=User.Role.ADMIN)

        tenant.owner = cls.owner
        tenant.name = "Test Tenant"
        return tenant

    def setUp(self):
        super().setUp()
        self.tenant.add_user(self.owner, is_superuser=True)
        self.client = TenantClient(self.tenant)
        self.client.force_login(user=self.owner)
        self.product = Product.objects.create(name="Test Product", version="1.0", owner=self.owner)
        self.report = Report.objects.create(title="a", description="a", steps_to_reproduce="a", email="a",
                                            product=self.product)

    def test_admin_permissions(self):
        self.client.force_login(user=self.owner)
        r = self.client.post(f"/products/{self.product.id}/report/", data={"title": "title", "description": "description", "steps_to_reproduce": "steps"})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        report_id = r.data["id"]
        r = self.client.put(f"/products/{self.product.id}/report/{report_id}/", data={"status": Report.Status.OPEN, "severity": Report.Severity.CRITICAL, "priority": Report.Priority.CRITICAL}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        r = self.client.put(f"/products/{self.product.id}/report/{report_id}/", data={"status": Report.Status.ASSIGNED}, content_type="application/json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)