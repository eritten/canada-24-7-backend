from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from accounts.models import Follow, UserProfile
from accounts.serializers import PublicUserSerializer
from canada247.api import paginated_response, success_response
from posts.models import Bookmark, Comment, Dislike, Like, Post, Repost
from posts.serializers import CommentSerializer, PostSerializer, toggle_post_reaction


class StandardPagination(PageNumberPagination):
    page_size = 20


class FeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category = self.request.query_params.get("category")
        queryset = Post.objects.select_related("author", "author__profile")
        if self.request.user.is_authenticated:
            followed_ids = Follow.objects.filter(follower=self.request.user).values_list("following_id", flat=True)
            queryset = queryset.filter(Q(author_id__in=followed_ids) | Q(author=self.request.user) | Q(is_news=True))
        if category:
            queryset = queryset.filter(category=category)
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class TrendingPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        since = timezone.now() - timedelta(hours=24)
        return (
            Post.objects.select_related("author", "author__profile")
            .annotate(recent_likes=Count("like", filter=Q(like__created_at__gte=since)))
            .order_by("-recent_likes", "-created_at")
        )

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class PostCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination
    queryset = Post.objects.select_related("author", "author__profile")

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Post created successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.select_related("author", "author__profile")

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object(), context={"request": request}).data)

    def put(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return success_response(message="You cannot edit this post.", status_code=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(post, data=request.data, partial=False, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Post updated successfully.", data=serializer.data)

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return success_response(message="You cannot delete this post.", status_code=status.HTTP_403_FORBIDDEN)
        post.delete()
        return success_response(message="Post deleted successfully.")


class PostLikeView(APIView):
    def post(self, request, pk):
        post = generics.get_object_or_404(Post, pk=pk)
        active = toggle_post_reaction(request.user, post, Like, opposite_model=Dislike)
        return success_response(message="Post like updated.", data={"active": active})


class PostDislikeView(APIView):
    def post(self, request, pk):
        post = generics.get_object_or_404(Post, pk=pk)
        active = toggle_post_reaction(request.user, post, Dislike, opposite_model=Like)
        return success_response(message="Post dislike updated.", data={"active": active})


class PostRepostView(APIView):
    def post(self, request, pk):
        post = generics.get_object_or_404(Post, pk=pk)
        obj, created = Repost.objects.get_or_create(user=request.user, post=post)
        if not created:
            obj.delete()
        return success_response(message="Post repost updated.", data={"active": created})


class PostBookmarkView(APIView):
    def post(self, request, pk):
        post = generics.get_object_or_404(Post, pk=pk)
        obj, created = Bookmark.objects.get_or_create(user=request.user, post=post)
        if not created:
            obj.delete()
        return success_response(message="Bookmark updated.", data={"active": created})


class BookmarkedPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Post.objects.select_related("author", "author__profile").filter(bookmarks__user=self.request.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class PostCommentsView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        post = generics.get_object_or_404(Post, pk=self.kwargs["pk"])
        return post.comments.filter(parent__isnull=True).select_related("author", "author__profile")

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)

    def create(self, request, *args, **kwargs):
        post = generics.get_object_or_404(Post, pk=self.kwargs["pk"])
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post)
        return success_response(message="Comment added successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED)


class CommentReplyView(APIView):
    def post(self, request, pk, comment_id):
        post = generics.get_object_or_404(Post, pk=pk)
        parent = generics.get_object_or_404(Comment, pk=comment_id, post=post)
        serializer = CommentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, post=post, parent=parent)
        return success_response(message="Reply added successfully.", data=serializer.data, status_code=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    def delete(self, request, comment_id):
        comment = generics.get_object_or_404(Comment, pk=comment_id)
        if comment.author != request.user:
            return success_response(message="You cannot delete this comment.", status_code=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return success_response(message="Comment deleted successfully.")


class CommentLikeView(APIView):
    def post(self, request, comment_id):
        comment = generics.get_object_or_404(Comment, pk=comment_id)
        obj, created = Like.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            obj.delete()
        return success_response(message="Comment like updated.", data={"active": created})


class GlobalSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        posts = Post.objects.select_related("author", "author__profile").filter(content__icontains=query)[:10]
        users = UserProfile.objects.select_related("user").filter(Q(username__icontains=query) | Q(user__full_name__icontains=query))[:10]
        news_posts = Post.objects.select_related("author", "author__profile").filter(is_news=True, content__icontains=query)[:10]
        return success_response(
            data={
                "posts": PostSerializer(posts, many=True, context={"request": request}).data,
                "users": PublicUserSerializer(users, many=True, context={"request": request}).data,
                "news": PostSerializer(news_posts, many=True, context={"request": request}).data,
            }
        )


class UserSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        users = UserProfile.objects.select_related("user").filter(Q(username__icontains=query) | Q(user__full_name__icontains=query))[:20]
        return success_response(data=PublicUserSerializer(users, many=True, context={"request": request}).data)


class PostSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        posts = Post.objects.select_related("author", "author__profile").filter(content__icontains=query)[:20]
        return success_response(data=PostSerializer(posts, many=True, context={"request": request}).data)
