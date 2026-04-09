from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


class SubclassUserAdmin(BaseUserAdmin):
    list_display = ('username', 'get_type')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password'),
        }),
    )

    def get_type(self, obj):
        return obj._meta.verbose_name

    get_type.short_description = 'Role'


class DeveloperAdmin(SubclassUserAdmin):
    pass


class ProductOwnerAdmin(SubclassUserAdmin):
    pass


admin.site.register(Product)
admin.site.register(Report)
admin.site.register(Developer, DeveloperAdmin)
admin.site.register(ProductOwner, ProductOwnerAdmin)
admin.site.register(Comment)