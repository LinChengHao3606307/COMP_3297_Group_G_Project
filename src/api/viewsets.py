from rest_framework import routers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSubmissionSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product__id", "product__name", "owner__id"]

    def get_serializer_class(self):
        if self.action == "comments":
            return CommentSerializer
        elif self.action == "evaluate":
            return ReportEvaluationSerializer
        elif self.action == "claim":
            return ReportClaimSerializer
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
            serializer = ReportSubmissionSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ReportEvaluationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if report.email:
                print(f"Email to {report.email}: Status updated to {report.status}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
        raise serializers.ValidationError("Method not allowed")

    @action(detail=True, methods=["GET", "PUT"], url_path="claim")
    def claim(self, request, pk=None):
        report = self.get_object()
        if request.method == "GET":
            serializer = ReportSubmissionSerializer(report, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            # 1. Pass the instance=report so the serializer knows WHICH report to represent in the return
            serializer = ReportClaimSerializer(report, data=request.data, context={'report': report})
            serializer.is_valid(raise_exception=True)
    
            # 2. Update and save
            report.developer = serializer.validated_data["developer"]
            report.status = Report.Status.ASSIGNED
            report.save()

            # 3. Handle the 'Email' (Good use of the saved instance!)
            if report.email:
            # report.get_status_display() will print "Assigned" instead of "ASGN"
                print(f"Email to {report.email}: Status updated to {report.get_status_display()}")

            # 4. Return the data (Now it will include the full nested developer JSON)
                return Response(serializer.data, status=status.HTTP_200_OK)

        raise serializers.ValidationError("Method not allowed")


router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reports', ReportViewSet, basename='report')