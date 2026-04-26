from django.contrib.auth.hashers import get_hasher, make_password
from django.test import TestCase

from ..models import *


class UserModelsTests(TestCase):
    def test_creation(self):
        # Random keyboard spam
        username_dev = "dfkon23r80ujfadiojn"
        password_dev = "dohjn32qr90uasfmk"
        username_po = "ihjsd89234uiohwef89y24"
        password_po = "jnsdio3qr280ijds90im23rklmsdi/."

        def test(model, username, password):
            hasher = get_hasher()
            user = model.objects.create_user(username=username, password=password)

            self.assertEqual(user.username, username)
            self.assertEqual(user.password, make_password(password, hasher.decode(user.password)["salt"]))
            self.assertTrue(user.check_password(password))

        test(Developer, username_dev, password_dev)
        test(ProductOwner, username_po, password_po)
