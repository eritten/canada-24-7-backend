from django.urls import path

from news import views


urlpatterns = [
    path("news/", views.NewsListView.as_view(), name="news-list"),
    path("news/favorites/", views.NewsFavoritesView.as_view(), name="news-favorites"),
    path("news/<str:category>/", views.NewsByCategoryView.as_view(), name="news-category"),
    path("news/<uuid:post_id>/favorite/", views.NewsFavoriteToggleView.as_view(), name="news-favorite-toggle"),
]
