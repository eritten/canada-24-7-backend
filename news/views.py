from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from canada247.api import paginated_response, success_response
from news.models import FavoriteNews
from posts.models import Post
from posts.serializers import PostSerializer


class StandardPagination(PageNumberPagination):
    page_size = 20


class NewsListView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Post.objects.select_related("author", "author__profile").filter(is_news=True)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)


class NewsByCategoryView(NewsListView):
    def get_queryset(self):
        return super().get_queryset().filter(category=self.kwargs["category"])


class NewsFavoriteToggleView(APIView):
    def post(self, request, post_id):
        post = generics.get_object_or_404(Post, pk=post_id, is_news=True)
        obj, created = FavoriteNews.objects.get_or_create(user=request.user, post=post)
        if not created:
            obj.delete()
        return success_response(message="Favorite updated.", data={"active": created})


class NewsFavoritesView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Post.objects.select_related("author", "author__profile").filter(favorited_by__user=self.request.user, is_news=True)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        serializer = self.get_serializer(page, many=True, context={"request": request})
        return paginated_response(self.paginator.get_paginated_response(serializer.data).data)
