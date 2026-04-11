from rest_framework import serializers

from news.models import FavoriteNews, NewsCategory
from posts.serializers import PostSerializer


class NewsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategory
        fields = ("id", "name", "slug", "icon")


class FavoriteNewsSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = FavoriteNews
        fields = ("id", "post", "created_at")
