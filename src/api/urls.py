from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .viewsets import ProductViewSet, ReportViewSet, UserViewSet
from django.urls import path, include
app_name = 'api'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'products', ProductViewSet, basename='products')

rp_router = nested_routers.NestedSimpleRouter(router, r'products', lookup='products')
rp_router.register(r'report', ReportViewSet, basename='report')

urlpatterns = [
    *router.urls,
    *rp_router.urls,
    path('api-auth/', include('rest_framework.urls'), name='api-root'),
]