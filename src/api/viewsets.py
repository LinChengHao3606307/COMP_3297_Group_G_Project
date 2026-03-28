from rest_framework import routers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import *


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "comments":
            return CommentSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # role = serializer.validated_data.pop("declared_role", None)
        # user_id = serializer.validated_data.pop("declared_user_id", None)
        # product_id = serializer.validated_data.pop("declared_product_id", None)
        #
        # try:
        #     user = User.objects.get(role=role, user_id=user_id)
        #     product = Product.objects.get(id=product_id)
        # except User.DoesNotExist:
        #     raise serializers.ValidationError("User does not exist")
        # except Product.DoesNotExist:
        #     raise serializers.ValidationError("Product does not exist")
        #
        # report = serializer.save(
        #     owner=user,
        #     product=product,
        #     status="New"
        # )

        report = serializer.save()

        if report.email:
            print(f"Email to {report.email}: Defect report {report.id} has been created.")

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["GET", "POST"], url_path="comments")
    def comments(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            comments = report.comments.all().order_by("created_at")
            serializer = CommentSerializer(comments, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "POST":
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            role = serializer.validated_data.pop("declared_role", None)
            user_id = serializer.validated_data.pop("declared_user_id", None)

            try:
                user = User.objects.get(role=role, user_id=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("User does not exist")

            comment = serializer.save(
                owner=user,
                report=report,
            )

            if report.email:
                print(f"Email to {report.email}: New comment from {user}: {comment.text}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        raise serializers.ValidationError("Method not allowed")



router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reports', ReportViewSet, basename='report')