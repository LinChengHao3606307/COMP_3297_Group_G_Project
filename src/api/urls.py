from django.urls import path, include
from .serializers import router
from .views import *

app_name = 'api'

urlpatterns = [
    path("product", product),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls'), name='api-root'),
]