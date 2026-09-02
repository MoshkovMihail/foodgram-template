from django.contrib import admin

from .models import CustomUser, Follow


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "id", "email", "first_name", "last_name")
    search_fields = ("first_name", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")
    readonly_fields = ("date_joined", "last_login")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "following")
    search_fields = ("user", "following")
    list_filter = ("user", "following")


admin.site.empty_value_display = "Не задано"
