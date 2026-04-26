from rest_framework import status
from rest_framework.test import APITestCase

from ..models import *

class BlankDatabaseTests(APITestCase):
    def test_base_link(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertHasAttr(r, "data")
        self.assertIn("products", r.data)
        self.assertIn("reports", r.data)
        self.assertIn("users", r.data)

    def test_create_users(self):
        username_dev = "uin89y34iomdvsm"
        password_dev = "sdfvioh24qt89ynjkf"
        username_po = "nuojdvs89023riondvsion235.sdv"
        password_po = "asd89yu3r2iond23bgwtrenyyu"

        def test(model, username, password, user_type):
            r = self.client.post("/users/", {"username": username, "password": password, "user_type": user_type})
            self.assertEqual(r.status_code, status.HTTP_201_CREATED)
            self.assertHasAttr(r, "data")
            self.assertIn("id", r.data)
            self.assertEqual(r.data["username"], username)

            self.assertEqual(model.objects.count(), 1)
            dev = model.objects.all()[0]
            self.assertEqual(dev.username, username)
            self.assertTrue(dev.check_password(password))

        test(Developer, username_dev, password_dev, "developer")
        test(ProductOwner, username_po, password_po, "product_owner")


class ProductsTests(APITestCase):
    def setUp(self):
        self.dev = Developer.objects.create_user(username='dev', password='dev')
        self.po = ProductOwner.objects.create_user(username='po', password='po')

    def test_create_product(self):
        # Success
        name = "product"
        version = "1.0.0"
        self.client.force_authenticate(user=self.po)
        r = self.client.post("/products/", {"name": name, "version": version})
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", r.data)
        self.assertIn("url", r.data)
        self.assertIn("reports_url", r.data)
        self.assertEqual(r.data["name"], name)
        self.assertEqual(r.data["version"], version)
        self.assertEqual(r.data["owner"]["username"], self.po.username)
