from django.urls import path

from posts import views


urlpatterns = [
    path("posts/feed/", views.FeedView.as_view(), name="posts-feed"),
    path("posts/trending/", views.TrendingPostsView.as_view(), name="posts-trending"),
    path("posts/", views.PostCreateView.as_view(), name="posts-create"),
    path("posts/bookmarks/", views.BookmarkedPostsView.as_view(), name="posts-bookmarks"),
    path("posts/<uuid:pk>/", views.PostDetailView.as_view(), name="posts-detail"),
    path("posts/<uuid:pk>/like/", views.PostLikeView.as_view(), name="posts-like"),
    path("posts/<uuid:pk>/dislike/", views.PostDislikeView.as_view(), name="posts-dislike"),
    path("posts/<uuid:pk>/repost/", views.PostRepostView.as_view(), name="posts-repost"),
    path("posts/<uuid:pk>/bookmark/", views.PostBookmarkView.as_view(), name="posts-bookmark"),
    path("posts/<uuid:pk>/comments/", views.PostCommentsView.as_view(), name="posts-comments"),
    path("posts/<uuid:pk>/comments/<uuid:comment_id>/reply/", views.CommentReplyView.as_view(), name="comments-reply"),
    path("comments/<uuid:comment_id>/", views.CommentDeleteView.as_view(), name="comments-delete"),
    path("comments/<uuid:comment_id>/like/", views.CommentLikeView.as_view(), name="comments-like"),
    path("search/", views.GlobalSearchView.as_view(), name="search-global"),
    path("search/users/", views.UserSearchView.as_view(), name="search-users"),
    path("search/posts/", views.PostSearchView.as_view(), name="search-posts"),
]
