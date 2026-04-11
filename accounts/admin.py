from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import CustomUser, Follow, OTPVerification, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "is_verified", "is_active", "is_staff", "created_at")
    search_fields = ("email", "full_name")
    list_filter = ("is_verified", "is_active", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password", "full_name")}),
        ("Permissions", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
    )
    readonly_fields = ("created_at", "last_login")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "password1", "password2", "is_staff", "is_superuser")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "location", "created_at")
    search_fields = ("username", "user__email", "user__full_name")


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "otp_code", "expires_at", "is_used", "created_at")
    search_fields = ("user__email",)
    list_filter = ("purpose", "is_used")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__email", "following__email")
