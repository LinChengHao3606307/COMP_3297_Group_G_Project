import json
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from django_tenants.utils import schema_context, get_public_schema_name

from ..models import Product, Report
from user_home.models import User

class IntegrationTests(TenantTestCase):
    @classmethod
    def setup_tenant(cls, tenant):
        # Create public tenant for user authentication
        try:
            create_public_tenant(
                domain_url="public.testserver",
                owner_email="public_admin@test.com"
            )
        except ExistsError:
            pass

        # Create users in the public schema
        with schema_context(get_public_schema_name()):
            cls.owner = User.objects.create_user(
                email="super@test.com", 
                password="password123", 
                role=User.Role.PRODUCT_OWNER
            )
            cls.tester = User.objects.create_user(
                email="tester@test.com", 
                password="password123", 
                role=User.Role.TESTER
            )
            cls.dev = User.objects.create_user(
                email="dev@test.com", 
                password="password123", 
                role=User.Role.DEVELOPER
            )

        tenant.owner = cls.owner
        tenant.name = "Test Tenant"
        return tenant

    def setUp(self):
        super().setUp()
        self.tenant.add_user(self.owner, is_superuser=True)
        self.tenant.add_user(self.tester)
        self.tenant.add_user(self.dev)
        self.client = TenantClient(self.tenant)

    def test_full_cycle(self):
        """Simulates the bug report lifecycle with proper JSON encoding and DB refreshes."""
        
        # --- STEP 1: PO creates a product ---
        self.client.force_login(user=self.owner)
        name = "AlphaApp"
        version = "1.0"
        r_prod = self.client.post("/products/", data={"name": name, "version": version})
        self.assertEqual(r_prod.status_code, status.HTTP_201_CREATED)

        # Get ID from DB since serializer doesn't return it
        product = Product.objects.get(name=name, version=version)
        product_id = product.id

        # --- STEP 2: Tester reports a bug ---
        self.client.force_login(user=self.tester)
        report_data = {
            "title": "Crash on startup",
            "description": "App crashes immediately",
            "steps_to_reproduce": "1. Open app.",
            "email": "user@customer.com"
        }
        r_rep = self.client.post(f"/products/{product_id}/report/", data=report_data)
        self.assertEqual(r_rep.status_code, status.HTTP_201_CREATED)
        
        report = Report.objects.get(title="Crash on startup", product=product)
        report_id = report.id

        # --- STEP 3: PO Evaluates (Sets to OPEN) ---
        # FIX: Must use JSON format and include required fields (Priority/Severity)
        self.client.force_login(user=self.owner)
        update_data = {
            "status": Report.Status.OPEN,
            "priority": Report.Priority.HIGH,
            "severity": Report.Severity.MAJOR
        }
        r_open = self.client.patch(
            f"/products/{product_id}/report/{report_id}/", 
            data=json.dumps(update_data), 
            content_type="application/json"
        )
        self.assertEqual(r_open.status_code, status.HTTP_200_OK)
        
        # CRITICAL: Update local variable from database
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.OPEN)

        # --- STEP 4: Developer Claims the report ---
        self.client.force_login(user=self.dev)
        r_claim = self.client.patch(
            f"/products/{product_id}/report/{report_id}/", 
            data=json.dumps({"status": Report.Status.ASSIGNED}), 
            content_type="application/json"
        )
        self.assertEqual(r_claim.status_code, status.HTTP_200_OK)
        
        # CRITICAL: Update local variable from database again
        report.refresh_from_db()
        self.assertEqual(report.status, Report.Status.ASSIGNED)
        self.assertEqual(report.assigned_to, self.dev)