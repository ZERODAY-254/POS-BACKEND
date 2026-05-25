from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ReturnViewSet


router = DefaultRouter()
router.register(r'returns', ReturnViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
