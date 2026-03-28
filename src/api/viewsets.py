from rest_framework import routers, viewsets, status
from rest_framework.response import Response

from .serializers import *


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.pop("declared_role", None)
        user_id = serializer.validated_data.pop("declared_user_id", None)
        product_id = serializer.validated_data.pop("declared_product_id", None)

        try:
            user = User.objects.get(role=role, user_id=user_id)
            product = Product.objects.get(id=product_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist")

        report = serializer.save(
            owner=user,
            product=product,
            status="New"
        )

        if report.email:
            print(f"Email to {report.email}: Defect report {report.id} has been created.")

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data.pop("declared_role", None)
        user_id = serializer.validated_data.pop("declared_user_id", None)
        report_id = serializer.validated_data.pop("declared_report_id", None)

        try:
            user = User.objects.get(role=role, user_id=user_id)
            report = Report.objects.get(id=report_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        except Report.DoesNotExist:
            raise serializers.ValidationError("Report does not exist")

        comment = serializer.save(
            owner=user,
            report=report,
        )

        if report.email:
            print(f"Email to {report.email}: New comment from {user}: {comment.text}")

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'users', UserViewSet, basename='user')
router.register(r'comments', CommentViewSet, basename='comment')