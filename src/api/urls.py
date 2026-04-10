from django.urls import path, include
from .viewsets import router

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
]