from django.contrib import admin
from user_home.admin import UserAdmin as BaseUserAdmin
from .models import *

class SubclassUserAdmin(BaseUserAdmin):
    list_display = ('id', 'email', 'get_type')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    def get_type(self, obj):
        return obj._meta.verbose_name

    get_type.short_description = 'Role'




admin.site.register(Product)
admin.site.register(Report)
admin.site.register(Comment)
