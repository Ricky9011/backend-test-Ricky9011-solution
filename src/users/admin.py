from django.contrib import admin

from src.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
