from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.test.testcases import TestCase, TransactionTestCase
from django_tenants.test.client import TenantClient
from django_tenants.test.cases import TenantTestCase
from tenant_users.tenants.utils import create_public_tenant, get_current_tenant
from django.db import connection

from ..models import *

class BlankDatabaseTests(TestCase):
    def setUp(self):
        self.tenant = create_public_tenant(domain_url='testserver', owner_email='super@test.com')
        self.owner = User.objects.get(email="super@test.com")
        self.owner.role = User.Role.PRODUCT_OWNER
        self.owner.save()
        self.test_tenant = Tenant.objects.create(name="test", owner=self.owner, schema_name="test")
        self.test_tenant.add_user(self.owner, is_superuser=True)
        connection.set_tenant(self.test_tenant)

        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        super().setUp()

    def test_base_link(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertHasAttr(r, "data")
        self.assertIn("products", r.data)
        self.assertIn("users", r.data)

    # def test_create_users(self):
    #     email_dev = "uin89y34iomdvsm@a.com"
    #     password_dev = "sdfvioh24qt89ynjkf"
    #     email_po = "nuojdvs89023riondvsion235.sdv@b.com"
    #     password_po = "asd89yu3r2iond23bgwtrenyyu"
    #
    #     def test(email, password, role):
    #         r = self.client.post("/users/", {"email": email, "password": password, "role": role})
    #         print(f"Schema at runtime: {connection.schema_name}")
    #         print(f"Response Data: {r.data}")  # Since it's DRF, check .data instead of .content
    #         self.assertEqual(r.status_code, status.HTTP_201_CREATED)
    #         self.assertHasAttr(r, "data")
    #         self.assertIn("id", r.data)
    #         self.assertEqual(r.data["email"], email)
    #
    #         self.assertEqual(User.objects.filter(role=role).count(), 1)
    #         user = User.objects.filter(role=role)[0]
    #         self.assertEqual(user.email, email)
    #         self.assertEqual(user.role, role)
    #         self.assertTrue(user.check_password(password))
    #
    #     test(email_dev, password_dev, User.Role.DEVELOPER)
    #     test(email_po, password_po, User.Role.PRODUCT_OWNER)

#
# class ProductsTests(APITestCase):
#     def setUp(self):
#         self.tenant = create_public_tenant(domain_url='testserver', owner_email='super@test.com')
#         self.owner = User.objects.get(email="super@test.com")
#         self.owner.role = User.Role.PRODUCT_OWNER
#         self.owner.save()
#         self.test_tenant = Tenant.objects.create(name="test", owner=self.owner, schema_name="test")
#         self.test_tenant.add_user(self.owner, is_superuser=True)
#
#         self.dev = User.objects.create_user(email='dev@test.com', password='dev', role=User.Role.DEVELOPER)
#         self.po = User.objects.create_user(email='po@test.com', password='po', role=User.Role.PRODUCT_OWNER)
#         connection.set_tenant(self.test_tenant)
#
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.owner)
#         super().setUp()
#
#     def test_create_product(self):
#         # Success
#         name = "product"
#         version = "1.0.0"
#         self.client.force_authenticate(user=self.po)
#         r = self.client.post("/products/", {"name": name, "version": version})
#         self.assertEqual(r.status_code, status.HTTP_201_CREATED)
#         self.assertIn("id", r.data)
#         self.assertIn("url", r.data)
#         self.assertIn("reports_url", r.data)
#         self.assertEqual(r.data["name"], name)
#         self.assertEqual(r.data["version"], version)
#         self.assertEqual(r.data["owner"]["username"], self.po.username)
