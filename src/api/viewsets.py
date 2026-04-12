from rest_framework import routers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import *
from .permissions import *


class ProductViewSet(viewsets.ModelViewSet):
    # TODO: add filter to get the product a PO owns
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsProductOwner()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "reports":
            return ProductInstanceReportSubmissionSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get', 'post'], url_path='reports')
    def reports(self, request, pk=None):
        product = self.get_object()
        if request.method == "POST":
            serializer = ProductInstanceReportSubmissionSerializer(data=request.data, context={"request": request, "product": product})
            serializer.is_valid(raise_exception=True)
            report = serializer.save(product=product, status="New")
            if report.email:
                print(f"Email to {report.email}: Defect report {report.id} has been created.")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        reports = product.reports.all().order_by('-id')
        serializer_display = ProductInstanceReportSubmissionSerializer(reports, many=True, context={'request': request})
        return Response(serializer_display.data)


class ReportViewSet(viewsets.ModelViewSet):
    # TODO: add filter to get the reports a developer is assigned to
    queryset = Report.objects.all()
    serializer_class = ReportDetailSerializer

    def get_permissions(self):
        if self.action in ["evaluate", "resolve"]:
            return [permissions.IsAuthenticated(), IsProductOwner()]
        elif self.action in ["claim", "fix"]:
            return [permissions.IsAuthenticated(), IsDeveloper()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return ReportSubmissionSerializer
        elif self.action == "update":
            return ReportUpdateSerializer
        elif self.action == "retrieve":
            return ReportDetailSerializer

        elif self.action == "comments":
            return CommentSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = serializer.save(status="New")

        if report.email:
            print(f"Email to {report.email}: Defect report {report.id} has been created.")

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Excluded by project assumption: undo changes
        # TODO: manage permissions using CanUpdateReportStatus
        # TODO: add duplicate status linkage handling
        # TODO (maybe): disallow changing severity and priority except for New reports; disallow changing assigned_to except for Open and Reopen reports
        report = self.get_object()
        serializer = self.get_serializer(report, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer_display = self.get_serializer(report)
        return Response(serializer_display.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        report = self.get_object()
        old_status = report.status

        serializer = self.get_serializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status", old_status)
        user = request.user

        # Product Owner actions
        if new_status in [Report.Status.OPEN, Report.Status.REJECTED, Report.Status.DUPLICATE]:
            if not IsProductOwner().has_permission(request, self):
                return Response({"error": "Only Product Owners can evaluate reports"}, status=403)

        # Developer actions
        if new_status in [Report.Status.ASSIGNED, Report.Status.FIXED]:
            if not IsDeveloper().has_permission(request, self):
                return Response({"error": "Only Developers can perform this action"}, status=403)

        if new_status == Report.Status.RESOLVED:
            if not IsProductOwner().has_permission(request, self):
                return Response({"error": "Only Product Owners can resolve reports"}, status=403)

        if new_status == Report.Status.ASSIGNED:
            serializer.save(assigned_to=user.developer)
        else:
            self.perform_update(serializer) 

        # Re-serialize
        serializer_display = self.get_serializer(report)
        return Response(serializer_display.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        # Excluded by project assumption: reflect changes immediately
        report = self.get_object()
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["GET", "POST"], url_path="comments")
    def comments(self, request, pk=None):
        # TODO (maybe): separate this to its own viewset to avoid nesting too much
        report = self.get_object()
        if request.method == "GET":
            comments = report.comments.all().order_by("created_at")
            serializer = CommentSerializer(comments, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "POST":
            serializer = CommentSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)

            comment = serializer.save(report=report)
            user = comment.author

            if report.email:
                print(f"Email to {report.email}: New comment from {user}: {comment.content}")

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        raise serializers.ValidationError("Method not allowed")


# Excluded by project assumption: implement front-end
router = routers.DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'reports', ReportViewSet, basename='report')
