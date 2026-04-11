from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from posts.models import Dislike, Like, Post


class PostReactionTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="user@example.com", password="Canada247x9", full_name="Test User", is_verified=True)
        self.other = CustomUser.objects.create_user(email="other@example.com", password="Canada247x9", full_name="Other User", is_verified=True)
        self.post = Post.objects.create(author=self.other, content="Test post", category="general")
        login = self.client.post("/api/auth/login/", {"email": self.user.email, "password": "Canada247x9"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")

    def test_like_removes_existing_dislike(self):
        Dislike.objects.create(user=self.user, post=self.post)

        response = self.client.post(f"/api/posts/{self.post.id}/like/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())
        self.assertFalse(Dislike.objects.filter(user=self.user, post=self.post).exists())
