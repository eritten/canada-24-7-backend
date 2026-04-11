from django.contrib import admin

from news.models import FavoriteNews, NewsCategory


admin.site.register(NewsCategory)
admin.site.register(FavoriteNews)
