# from django.contrib.auth.hashers import get_hasher, make_password
# from tenant_users.tenants.utils import create_public_tenant
# from django.test import TestCase
#
# from ..models import *
#
#
# class UserModelsTests(TestCase):
#     def setUp(self):
#         self.tenant = create_public_tenant(
#             domain_url='a.localhost',
#             owner_email='admin@test.com',
#         )
#
#     def test_creation(self):
#         # Random keyboard spam
#         email_dev = "dfkon23r80ujfadiojn@a.com"
#         password_dev = "dohjn32qr90uasfmk"
#         email_po = "ihjsd89234uiohwef89y24@b.com"
#         password_po = "jnsdio3qr280ijds90im23rklmsdi/."
#
#         def test(email, password, role):
#             hasher = get_hasher()
#             user = User.objects.create_user(email=email, password=password, role=role)
#
#             self.assertEqual(user.email, email)
#             self.assertEqual(user.role, role)
#             self.assertEqual(user.password, make_password(password, hasher.decode(user.password)["salt"]))
#             self.assertTrue(user.check_password(password))
#
#         test(email_dev, password_dev, User.Role.DEVELOPER)
#         test(email_po, password_po, User.Role.PRODUCT_OWNER)
