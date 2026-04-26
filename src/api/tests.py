from django.contrib.auth.hashers import get_hasher, make_password
from django.test import TestCase

from .models import Developer, ProductOwner


class UserModelsTests(TestCase):
    def test_creation(self):
        username_dev = "dfkon23r80ujfadiojn"
        password_dev = "dohjn32qr90uasfmk"
        username_po = "ihjsd89234uiohwef89y24"
        password_po = "jnsdio3qr280ijds90im23rklmsdi/."
        hasher = get_hasher()
        self.dev = Developer.objects.create_user(username=username_dev, password=password_dev)
        self.po = ProductOwner.objects.create_user(username=username_po, password=password_po)

        self.assertEqual(self.dev.username, username_dev)
        self.assertEqual(self.dev.password, make_password(password_dev, hasher.decode(self.dev.password)["salt"]))
        self.assertEqual(str(self.dev), f"Developer '{username_dev}'")

        self.assertEqual(self.po.username, username_po)
        self.assertEqual(self.po.password, make_password(password_po, hasher.decode(self.po.password)["salt"]))
        self.assertEqual(str(self.po), f"Product Owner '{username_po}'")

