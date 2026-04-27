from django.contrib.auth.hashers import get_hasher, make_password
from tenant_users.tenants.utils import create_public_tenant
from django.test import TestCase

from ..models import *


class UserModelsTests(TestCase):
    def setUp(self):
        self.tenant = create_public_tenant(
            domain_url='a.localhost',
            owner_email='admin@test.com',
        )

    def test_creation(self):
        # Random keyboard spam
        email_dev = "dfkon23r80ujfadiojn@a.com"
        password_dev = "dohjn32qr90uasfmk"
        email_po = "ihjsd89234uiohwef89y24@b.com"
        password_po = "jnsdio3qr280ijds90im23rklmsdi/."

        def test(email, password, role):
            hasher = get_hasher()
            user = User.objects.create_user(email=email, password=password, role=role)

            self.assertEqual(user.email, email)
            self.assertEqual(user.role, role)
            self.assertEqual(user.password, make_password(password, hasher.decode(user.password)["salt"]))
            self.assertTrue(user.check_password(password))

        test(email_dev, password_dev, User.Role.DEVELOPER)
        test(email_po, password_po, User.Role.PRODUCT_OWNER)


# class ProductModelTests(TestCase):
#     def setUp(self):
#         self.tenant = create_public_tenant(
#             domain_url='a.localhost',
#             owner_email='admin@test.com',
#         )
#         self.owner = User.objects.create(email="a@b.c", role=User.Role.PRODUCT_OWNER)
#
#     def test_creation(self):
#         name = "Product Name"
#         version = "1.0"
#
#         product = Product.objects.create(name=name, version=version, owner=self.owner)
#
#         self.assertEqual(product.name, name)
#         self.assertEqual(product.version, version)
#         self.assertEqual(product.owner, self.owner)
#
#
# class ReportModelTests(TestCase):
#     def setUp(self):
#         self.tenant = create_public_tenant(domain_url='a.localhost', owner_email='a@b.c')
#         self.owner = User.objects.create(email="a@b.c", role=User.Role.PRODUCT_OWNER)
#         self.product = Product.objects.create(name="Product", version="1.0", owner=self.owner)