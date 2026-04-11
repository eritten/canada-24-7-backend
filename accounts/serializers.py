import random

from django.contrib.auth import authenticate, password_validation
from django.core.cache import cache
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser, Follow, OTPVerification, UserProfile, validate_username
from accounts.tasks import send_otp_email_task
from canada247.api import sanitize_text


def enforce_otp_rate_limit(email, purpose):
    cache_key = f"otp-rate:{purpose}:{email.lower()}"
    current = cache.get(cache_key, 0)
    if current >= 3:
        raise serializers.ValidationError({"email": ["Too many OTP requests. Try again later."]})
    cache.set(cache_key, current + 1, timeout=60 * 60)


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        attrs["full_name"] = sanitize_text(attrs["full_name"])
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        if not any(char.isdigit() for char in attrs["password"]):
            raise serializers.ValidationError({"password": ["Password must contain at least one number."]})
        password_validation.validate_password(attrs["password"])
        if CustomUser.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError({"email": ["A user with this email already exists."]})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"].lower()
        enforce_otp_rate_limit(email, OTPVerification.PURPOSE_VERIFY)
        user = CustomUser.objects.create_user(
            email=email,
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            is_verified=False,
        )
        otp = generate_otp()
        OTPVerification.objects.create(user=user, otp_code=otp, purpose=OTPVerification.PURPOSE_VERIFY)
        send_otp_email_task.delay(user.email, otp, "Verify your Canada 24/7 account")
        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email__iexact=attrs["email"])
        except CustomUser.DoesNotExist as exc:
            raise serializers.ValidationError({"email": ["User not found."]}) from exc

        otp = OTPVerification.objects.filter(
            user=user,
            otp_code=attrs["otp_code"],
            purpose=OTPVerification.PURPOSE_VERIFY,
            is_used=False,
        ).first()
        if not otp or otp.is_expired():
            raise serializers.ValidationError({"otp_code": ["OTP is invalid or expired."]})
        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp = self.validated_data["otp"]
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return issue_tokens(user)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=OTPVerification.PURPOSE_CHOICES, default=OTPVerification.PURPOSE_VERIFY, write_only=True)

    def validate_email(self, value):
        if not CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User not found.")
        return value.lower()

    def save(self):
        email = self.validated_data["email"]
        purpose = self.validated_data["purpose"]
        enforce_otp_rate_limit(email, purpose)
        user = CustomUser.objects.get(email__iexact=email)
        OTPVerification.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        otp = generate_otp()
        OTPVerification.objects.create(user=user, otp_code=otp, purpose=purpose)
        send_otp_email_task.delay(user.email, otp, "Your Canada 24/7 security code")
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"].lower(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError({"detail": ["Invalid credentials."]})
        if not user.is_verified:
            raise serializers.ValidationError({"detail": ["Please verify your email before logging in."]})
        attrs["user"] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User not found.")
        return value.lower()

    def save(self):
        email = self.validated_data["email"]
        enforce_otp_rate_limit(email, OTPVerification.PURPOSE_RESET)
        user = CustomUser.objects.get(email__iexact=email)
        OTPVerification.objects.filter(user=user, purpose=OTPVerification.PURPOSE_RESET, is_used=False).update(is_used=True)
        otp = generate_otp()
        OTPVerification.objects.create(user=user, otp_code=otp, purpose=OTPVerification.PURPOSE_RESET)
        send_otp_email_task.delay(user.email, otp, "Reset your Canada 24/7 password")
        return user


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})
        if not any(char.isdigit() for char in attrs["new_password"]):
            raise serializers.ValidationError({"new_password": ["Password must contain at least one number."]})
        try:
            user = CustomUser.objects.get(email__iexact=attrs["email"])
        except CustomUser.DoesNotExist as exc:
            raise serializers.ValidationError({"email": ["User not found."]}) from exc

        otp = OTPVerification.objects.filter(
            user=user,
            otp_code=attrs["otp_code"],
            purpose=OTPVerification.PURPOSE_RESET,
            is_used=False,
        ).first()
        if not otp or otp.is_expired():
            raise serializers.ValidationError({"otp_code": ["OTP is invalid or expired."]})
        password_validation.validate_password(attrs["new_password"], user)
        attrs["user"] = user
        attrs["otp"] = otp
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp = self.validated_data["otp"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", required=False)
    email = serializers.EmailField(source="user.email", read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "full_name",
            "email",
            "username",
            "bio",
            "avatar",
            "cover_photo",
            "location",
            "website",
            "created_at",
            "followers_count",
            "following_count",
            "posts_count",
        )

    def get_followers_count(self, obj):
        return obj.user.follower_relationships.count()

    def get_following_count(self, obj):
        return obj.user.following_relationships.count()

    def get_posts_count(self, obj):
        return obj.user.posts.count()

    def validate_username(self, value):
        validate_username(value)
        qs = UserProfile.objects.filter(username__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for field in ("bio", "location"):
            if field in validated_data:
                validated_data[field] = sanitize_text(validated_data[field])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if "full_name" in user_data:
            instance.user.full_name = sanitize_text(user_data["full_name"])
            instance.user.save(update_fields=["full_name"])
        instance.save()
        return instance


class PublicUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name")
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("username", "full_name", "bio", "avatar", "location", "website", "is_following")

    def get_is_following(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(follower=request.user, following=obj.user).exists()
