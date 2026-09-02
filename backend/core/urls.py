from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from recipes.views import redirect_short_link

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.authtoken")),
    path("api/", include("recipes.urls")),
    path("s/<str:short_hash>/", redirect_short_link, name="short-link"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
