from django.urls import path, include

from .serializers import router

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls'), name='api-root'),
]