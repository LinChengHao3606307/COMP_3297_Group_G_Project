from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from django.core.exceptions import ValidationError
from .models import *
from tenant_users.tenants.models import TenantBase, UserProfileManager

class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ["schema_name"]

    def delete_model(self, request, obj):
        obj.delete(force_drop=True)

class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]

class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "role"]
    list_display_links = ["id", "email"]
    search_fields = ["email"]
    
    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_'):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if obj.id in Tenant.objects.values_list("owner_id", flat=True):
            raise ValidationError("You cannot delete a user that is a tenant owner.")
        # not truely deleting a user, refering to https://django-tenant-users.readthedocs.io/en/latest/pages/concepts.html#handling-user-and-tenant-deletion
        UserProfileManager().delete_user(obj)

admin.site.register(Tenant, TenantAdmin)
admin.site.register(Domain, DomainAdmin)
admin.site.register(User, UserAdmin)