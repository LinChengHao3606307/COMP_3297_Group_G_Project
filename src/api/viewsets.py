from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from .serializers import *
from .permissions import *
from tenant_users.tenants.utils import get_current_tenant

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        current_tenant = get_current_tenant()
        return current_tenant.user_set.all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['register', 'login', "create"]:
            return [permissions.AllowAny()]
        else:
            if self.action in ["destroy", "update", "partial_update"]:
                return [permissions.IsAuthenticated(), IsProductOwner()]
            return [permissions.IsAuthenticated()]

    def _validate_email_domain(self, email):
        current_domain = self.request.get_host().split(':')[0]
        if '@' not in email:
            raise ValidationError({"email": "this is not a valid email address!"})
        _, email_domain = email.split('@', 1)
        if email_domain != current_domain:
            raise ValidationError({
                "email": f"only allowed to create user under {current_domain}!"
            })
        
    def create(self, request, *args, **kwargs):

        email = request.data.get('email', '')
        self._validate_email_domain(email)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ProductCreationSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated()]
        if self.action in ["update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsProductOwner()]
        if self.action in ['get_by_owner']:
            return [permissions.IsAuthenticated(), IsProjectMember()]
        return [permissions.IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path=r'(?P<email_prefix>[a-zA-Z_][\w-]*)')
    def get_by_owner(self, request, email_prefix=None):
        email = f"{email_prefix}@{request.get_host().split(':')[0]}"
        products = Product.objects.filter(owner__email=email)
        if len(products):
            serializer = self.get_serializer(products, many=True, context={'request': request})
            return Response(serializer.data)
        if User.objects.filter(email=email).exists():
            return Response({'message': 'This product owner has no products.'}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)



class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportDetailSerializer

    def get_queryset(self):
        product_pk = self.kwargs.get("products_pk")
        return Report.objects.filter(product_id=product_pk)
    
    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), IsTester()]
        if self.action in ["evaluate", "resolve"]:
            return [permissions.IsAuthenticated(), IsProductOwner()]
        elif self.action in ["claim", "fix"]:
            return [permissions.IsAuthenticated(), IsDeveloper()]
        if self.action in ["update", "partial_update", "get_by_dev"]:
            return [permissions.IsAuthenticated(), IsProjectMember()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return ReportSubmissionSerializer
        elif self.action == "update":
            return ReportUpdateSerializer
        elif self.action == "retrieve":
            return ReportDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        product_pk = self.kwargs.get("products_pk")
        product = get_object_or_404(Product, id=product_pk)
        email = request.data.get('email') if request.data.get('email') else request.user.email
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(status=Report.Status.NEW, product=product, email=email)
        if report.email:
            print(f"Email to {report.email}: Defect report {report.title} has been created.")
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        report = self.get_object()
        old_status = report.status

        serializer = self.get_serializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status", old_status)
        user = request.user
        # Product Owner actions
        if new_status in [Report.Status.OPEN, Report.Status.REJECTED, Report.Status.DUPLICATE, Report.Status.REOPENED, Report.Status.RESOLVED]:
            if not IsProductOwner().has_permission(request, self):
                return Response({"error": "Only Product Owners can perform this action"}, status=403)
            if not IsProductOwner().has_object_permission(request, self, report):
                return Response({"error": "You do not have permission to modify this report"}, status=403)

        # Developer actions
        if new_status in [Report.Status.ASSIGNED, Report.Status.FIXED, Report.Status.CANNOT_REPRODUCE]:
            if not IsDeveloper().has_permission(request, self):
                return Response({"error": "Only Developers can perform this action"}, status=403)
            if not IsDeveloper().has_object_permission(request, self, report) and new_status != Report.Status.ASSIGNED:
                return Response({"error": "You do not have permission to modify this report"}, status=403)
            
        if new_status == Report.Status.OPEN:
            serializer.save(assigned_to=None, duplicated_to=None)
        elif new_status == Report.Status.ASSIGNED:
            serializer.save(assigned_to=user, duplicated_to=None)
        elif new_status == Report.Status.DUPLICATE:
            duplicate_report = serializer.validated_data.get("duplicated_to")
            priority = duplicate_report.priority
            severity = duplicate_report.severity
            serializer.save(duplicated_to=duplicate_report, status=Report.Status.DUPLICATE, priority=priority, severity=severity, assigned_to=None)
        else:
            serializer.save(duplicated_to=None)

        # Re-serialize
        serializer_display = self.get_serializer(report)
        if report.email:
            print(f"Email to {report.email}: Defect report {report.title} has been updated.")
        return Response(serializer_display.data, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        order = request.GET.get('orderByTime', 'none')
        order = order.lower()
        if order not in ['asc', 'desc']:
            return super().list(request, *args, **kwargs)
        reports = Report.objects.all().order_by('-updated_at' if order == 'desc' else 'updated_at')
        serializer = self.get_serializer(reports, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'(?P<email_prefix>[a-zA-Z_][\w-]*)')
    def get_by_dev(self, request, email_prefix=None):
        email = f"{email_prefix}@{request.get_host().split(':')[0]}"
        product_pk = self.kwargs.get("products_pk")
        reports = Report.objects.filter(assigned_to__isnull=False, assigned_to__email=email, product_id=product_pk)
        if len(reports):
            order = request.GET.get('orderByTime', 'none')
            order = order.lower()
            if order in ['asc', 'desc']:
                reports = reports.order_by('-updated_at' if order == 'desc' else 'updated_at')
            serializer = self.get_serializer(reports, many=True, context={'request': request})
            return Response(serializer.data)
        if User.objects.filter(email=email).exists():
            return Response({'message': 'This developer has not yet assigned any reports.'}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        report_pk = self.kwargs.get("report_pk")
        return Comment.objects.filter(
            report_id=report_pk,
        ).order_by('created_at')

    def get_permissions(self):
        if self.action in ["list", "detail", "create", "destroy", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsProjectMember()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        report_pk = self.kwargs.get('report_pk')
        if report_pk is not None:
            return Comment.objects.filter(report_id=report_pk).order_by('created_at')
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        report_pk = self.kwargs.get('report_pk')
        if report_pk is None:
            return Response({"detail": "report id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = Report.objects.get(pk=report_pk)
        except Report.DoesNotExist:
            return Response({"detail": "report not found"}, status=status.HTTP_404_NOT_FOUND)

        author = request.user if request.user and request.user.is_authenticated else None

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(report=report, author=author)

        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(comment).data, status=status.HTTP_201_CREATED, headers=headers)
    