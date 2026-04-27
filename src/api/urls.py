from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .viewsets import UserViewSet, DeveloperMetricsViewSet, ProductViewSet, ReportViewSet, CommentViewSet
app_name = 'api'

router = DefaultRouter()
router.register(r'developer-metrics', DeveloperMetricsViewSet, basename='developer-metrics')
router.register(r'users', UserViewSet, basename='users')
router.register(r'products', ProductViewSet, basename='products')

rp_router = nested_routers.NestedSimpleRouter(router, r'products', lookup='products')
rp_router.register(r'report', ReportViewSet, basename='report')

cm_router = nested_routers.NestedSimpleRouter(rp_router, r'report', lookup='report')
cm_router.register(r'comments', CommentViewSet, basename='comments')

urlpatterns = [
    *router.urls,
    *rp_router.urls,
    *cm_router.urls
]