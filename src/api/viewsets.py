from rest_framework import routers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=['get'], url_path='reports')
    def reports(self, request, pk=None):
        product = self.get_object()
        reports = product.reports.all().order_by('-id')

        serializer = ReportSubmissionSerializer(reports, many=True, context={'request': request})
        return Response(serializer.data)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ["owner__id"]

    def get_serializer_class(self):
        if self.action == "create":
            return ReportSubmissionSerializer
        elif self.action == "comments":
            return CommentSerializer
        elif self.action == "evaluate":
            return ReportEvaluationSerializer
        elif self.action == "claim":
            return ReportClaimSerializer
        elif self.action == "fix":
            return ReportFixSerializer
        elif self.action == "resolve":
            return ReportResolveSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = serializer.save(status="New")

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

            comment = serializer.save(report=report)
            user = comment.owner

            if report.email:
                print(f"Email to {report.email}: New comment from {user}: {comment.text}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        raise serializers.ValidationError("Method not allowed")

    @action(detail=True, methods=["GET", "PUT"], url_path="evaluate")
    def evaluate(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            serializer = ReportDetailSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ReportEvaluationSerializer(report, data=request.data, context={'report': report})
            serializer.is_valid(raise_exception=True)

            report.status = serializer.validated_data["status"]
            report.severity = serializer.validated_data["severity"]
            report.priority = serializer.validated_data["priority"]
            report.save()
            if report.email:
                print(f"Email to {report.email}: Status updated to {report.status}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
        raise serializers.ValidationError("Method not allowed")

    @action(detail=True, methods=["GET", "PUT"], url_path="claim")
    def claim(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            serializer = ReportDetailSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ReportClaimSerializer(report, data=request.data, context={'report': report})
            serializer.is_valid(raise_exception=True)
    
            report.developer = serializer.validated_data["developer"]
            report.status = serializer.validated_data["status"]
            report.save()

            if report.email:
                print(f"Email to {report.email}: Status updated to {report.get_status_display()}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

        raise serializers.ValidationError("Method not allowed")

    @action(detail=True, methods=["GET", "PUT"], url_path="fix")
    def fix(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            serializer = ReportDetailSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ReportFixSerializer(report, data=request.data, context={'report': report})
            serializer.is_valid(raise_exception=True)
            report.status = serializer.validated_data["status"]
            report.save()

            if report.email:
                print(f"Email to {report.email}: Status updated to {report.status}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
        raise serializers.ValidationError("Method not allowed")

    @action(detail=True, methods=["GET", "PUT"], url_path="resolve")
    def resolve(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            serializer = ReportDetailSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ReportResolveSerializer(report, data=request.data, context={'report': report})
            serializer.is_valid(raise_exception=True)
            report.status = serializer.validated_data["status"]
            report.save()
            if report.email:
                print(f"Email to {report.email}: Status updated to {report.status}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reports', ReportViewSet, basename='report')