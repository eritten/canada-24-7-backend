import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Post(models.Model):
    MEDIA_IMAGE = "image"
    MEDIA_VIDEO = "video"
    MEDIA_NONE = "none"
    MEDIA_CHOICES = ((MEDIA_IMAGE, "Image"), (MEDIA_VIDEO, "Video"), (MEDIA_NONE, "None"))
    CATEGORY_CHOICES = (
        ("politics", "Politics"),
        ("sports", "Sports"),
        ("entertainment", "Entertainment"),
        ("business", "Business"),
        ("technology", "Technology"),
        ("health", "Health"),
        ("weather", "Weather"),
        ("general", "General"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(max_length=500)
    media = models.FileField(upload_to="posts/", blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES, default=MEDIA_NONE)
    is_news = models.BooleanField(default=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.email}: {self.content[:40]}"


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField(max_length=300)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.email}: {self.content[:40]}"


class ReactionBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def clean(self):
        if bool(self.post) == bool(self.comment):
            raise ValidationError("Reaction must target either a post or a comment.")


class Like(ReactionBase):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], condition=models.Q(post__isnull=False), name="unique_post_like"),
            models.UniqueConstraint(fields=["user", "comment"], condition=models.Q(comment__isnull=False), name="unique_comment_like"),
        ]

    def __str__(self):
        return f"Like by {self.user.email}"


class Dislike(ReactionBase):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], condition=models.Q(post__isnull=False), name="unique_post_dislike"),
            models.UniqueConstraint(fields=["user", "comment"], condition=models.Q(comment__isnull=False), name="unique_comment_dislike"),
        ]

    def __str__(self):
        return f"Dislike by {self.user.email}"


class Repost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reposts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reposts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_repost")]

    def __str__(self):
        return f"{self.user.email} reposted {self.post_id}"


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_bookmark")]

    def __str__(self):
        return f"{self.user.email} bookmarked {self.post_id}"
