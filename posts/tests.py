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


class PublicContentTests(APITestCase):
    def setUp(self):
        self.author = CustomUser.objects.create_user(email="author@example.com", password="Canada247x9", full_name="Author User", is_verified=True)
        self.news_author = CustomUser.objects.create_user(email="news@example.com", password="Canada247x9", full_name="News Desk", is_verified=True)
        self.post = Post.objects.create(author=self.author, content="Public community post", category="general")
        self.news_post = Post.objects.create(author=self.news_author, content="Breaking public news", category="politics", is_news=True)

    def test_guest_can_view_feed(self):
        response = self.client.get("/api/posts/feed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["data"]["count"], 1)

    def test_guest_can_view_post_detail_and_comments(self):
        detail_response = self.client.get(f"/api/posts/{self.post.id}/")
        comments_response = self.client.get(f"/api/posts/{self.post.id}/comments/")

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(comments_response.status_code, status.HTTP_200_OK)

    def test_guest_can_search_and_view_news(self):
        search_response = self.client.get("/api/search/", {"q": "public"})
        news_response = self.client.get("/api/news/")

        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(news_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(news_response.data["data"]["count"], 1)
