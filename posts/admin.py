from django.contrib import admin

from posts.models import Bookmark, Comment, Dislike, Like, Post, Repost


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "category", "is_news", "created_at")
    search_fields = ("author__email", "content")
    list_filter = ("category", "is_news")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    search_fields = ("author__email", "content")


admin.site.register(Like)
admin.site.register(Dislike)
admin.site.register(Repost)
admin.site.register(Bookmark)
