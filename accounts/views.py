from django.db.models import Count
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Follow, UserProfile
from accounts.serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
    issue_tokens,
)
from canada247.api import paginated_response, success_response
from posts.models import Post
from posts.serializers import PostSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Registration successful. Please verify your email.", status_code=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.save()
        return success_response(message="Email verified successfully.", data=tokens)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="OTP sent successfully.")


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(message="Login successful.", data=issue_tokens(serializer.validated_data["user"]))


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"success": False, "message": "Refresh token is required.", "errors": {"refresh": ["This field is required."]}}, status=status.HTTP_400_BAD_REQUEST)
        RefreshToken(refresh).blacklist()
        return success_response(message="Logged out successfully.")


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password reset OTP sent successfully.")


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password reset successfully.")


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user.profile

    def get(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object()).data)

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Profile updated successfully.", data=serializer.data)


class PublicProfileView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    lookup_field = "username"
    queryset = UserProfile.objects.select_related("user")

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), context={"request": request})
        return success_response(data=serializer.data)


class FeedPagination(PageNumberPagination):
    page_size = 20


class PublicProfilePostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        profile = generics.get_object_or_404(UserProfile, username=self.kwargs["username"])
        return Post.objects.select_related("author", "author__profile").filter(author=profile.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class ProfileFollowersView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        profile = generics.get_object_or_404(UserProfile, username=self.kwargs["username"])
        return UserProfile.objects.filter(user__following_relationships__following=profile.user).select_related("user")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class ProfileFollowingView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        profile = generics.get_object_or_404(UserProfile, username=self.kwargs["username"])
        return UserProfile.objects.filter(user__follower_relationships__follower=profile.user).select_related("user")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class FollowToggleView(APIView):
    def post(self, request, username):
        profile = generics.get_object_or_404(UserProfile, username=username)
        Follow.objects.get_or_create(follower=request.user, following=profile.user)
        return success_response(message="User followed successfully.")

    def delete(self, request, username):
        profile = generics.get_object_or_404(UserProfile, username=username)
        Follow.objects.filter(follower=request.user, following=profile.user).delete()
        return success_response(message="User unfollowed successfully.")


class FollowSuggestionsView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        followed_ids = Follow.objects.filter(follower=self.request.user).values_list("following_id", flat=True)
        return (
            UserProfile.objects.select_related("user")
            .exclude(user=self.request.user)
            .exclude(user_id__in=followed_ids)
            .annotate(follower_total=Count("user__follower_relationships"))
            .order_by("-follower_total", "-created_at")
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)
