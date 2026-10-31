from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("criminals", views.WantedCriminalViewSet)
router.register("hunts", views.HuntLogViewSet)


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health),
    path("api/", include(router.urls)),
]
