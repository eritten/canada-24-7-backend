from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from canada247 import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health/", views.health, name="health"),
    path("api/", include("accounts.urls")),
    path("api/", include("posts.urls")),
    path("api/", include("news.urls")),
    path("api/", include("notifications.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
