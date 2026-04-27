from django.db import models
from tenant_users.tenants.models import TenantBase, UserProfile
from django_tenants.models import DomainMixin

class Tenant(TenantBase):
    name = models.CharField(max_length=100)

class Domain(DomainMixin):
    pass

class User(UserProfile):
    class Role(models.TextChoices):
        PRODUCT_OWNER = "PO", "Product Owner"
        DEVELOPER = "DEV", "Developer"
        TESTER = "TESTER", "Tester"
        ADMIN = "ADM", "Tenant Administrator"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.ADMIN,
        db_index=True
    )

    fixed_report = models.IntegerField(default=0)

    reopened_report = models.IntegerField(default=0)

    @property
    def is_product_owner(self):
        return self.role == self.Role.PRODUCT_OWNER

    @property
    def is_developer(self):
        return self.role == self.Role.DEVELOPER

    @property
    def is_tester(self):
        return self.role == self.Role.TESTER