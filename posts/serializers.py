from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from canada247.api import sanitize_text
from posts.models import Bookmark, Comment, Dislike, Like, Post, Repost


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.profile.username", read_only=True)
    author_full_name = serializers.CharField(source="author.full_name", read_only=True)
    author_avatar = serializers.ImageField(source="author.profile.avatar", read_only=True)
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    repost_count = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "author_username",
            "author_full_name",
            "author_avatar",
            "content",
            "media",
            "media_type",
            "is_news",
            "category",
            "created_at",
            "updated_at",
            "like_count",
            "dislike_count",
            "comment_count",
            "repost_count",
            "is_bookmarked",
        )
        read_only_fields = ("author",)

    def get_like_count(self, obj):
        return obj.like_set.count()

    def get_dislike_count(self, obj):
        return obj.dislike_set.count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_repost_count(self, obj):
        return obj.reposts.count()

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return Bookmark.objects.filter(user=request.user, post=obj).exists()

    def validate_content(self, value):
        value = sanitize_text(value)
        if not value:
            raise serializers.ValidationError("Post content cannot be empty.")
        return value

    def validate(self, attrs):
        media = attrs.get("media")
        media_type = attrs.get("media_type", Post.MEDIA_NONE)
        if media and media_type == Post.MEDIA_NONE:
            raise serializers.ValidationError({"media_type": ["Media type must be set when uploading media."]})
        return attrs

    def create(self, validated_data):
        return Post.objects.create(author=self.context["request"].user, **validated_data)

    def update(self, instance, validated_data):
        if timezone.now() > instance.created_at + timedelta(minutes=15):
            raise serializers.ValidationError({"detail": ["Posts can only be edited within 15 minutes of publishing."]})
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.profile.username", read_only=True)
    author_full_name = serializers.CharField(source="author.full_name", read_only=True)
    like_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "author_username",
            "author_full_name",
            "content",
            "parent",
            "created_at",
            "like_count",
            "replies",
        )
        read_only_fields = ("author", "post")

    def get_like_count(self, obj):
        return obj.like_set.count()

    def get_replies(self, obj):
        if obj.parent_id:
            return []
        return CommentSerializer(obj.replies.all(), many=True, context=self.context).data

    def validate_content(self, value):
        value = sanitize_text(value)
        if not value:
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value


@transaction.atomic
def toggle_post_reaction(user, post, model, opposite_model=None):
    obj, created = model.objects.get_or_create(user=user, post=post)
    if not created:
        obj.delete()
        return False
    if opposite_model:
        opposite_model.objects.filter(user=user, post=post).delete()
    return True
