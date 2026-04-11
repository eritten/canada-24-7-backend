from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts import views


urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend-otp/", views.ResendOTPView.as_view(), name="resend-otp"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("auth/reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
    path("profile/me/", views.MyProfileView.as_view(), name="my-profile"),
    path("profile/<str:username>/", views.PublicProfileView.as_view(), name="public-profile"),
    path("profile/<str:username>/posts/", views.PublicProfilePostsView.as_view(), name="public-profile-posts"),
    path("profile/<str:username>/followers/", views.ProfileFollowersView.as_view(), name="profile-followers"),
    path("profile/<str:username>/following/", views.ProfileFollowingView.as_view(), name="profile-following"),
    path("follow/<str:username>/", views.FollowToggleView.as_view(), name="follow-toggle"),
    path("follow/suggestions/", views.FollowSuggestionsView.as_view(), name="follow-suggestions"),
]
