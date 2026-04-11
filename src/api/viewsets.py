from rest_framework import routers, viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate, login, logout
from .serializers import *
from .permissions import *

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == "login":
            return UserLoginSerializer
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'register':
            return [permissions.AllowAny()]
        elif self.action == 'login':
            return [permissions.AllowAny()]
        else:
            if self.action in ["create", "destroy", "update", "partial_update"]:
                return [permissions.IsAuthenticated(), IsProductOwner()]
            return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get', 'post'], url_path='register')
    def register(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get', 'post'], url_path='login')
    def login(self, request):
        if request.method == 'GET':
            return Response({"message": "please login via POST"}, status=405)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                "message": "login success",
                "user": UserSerializer(user).data,
                "view products" : request.build_absolute_uri(f'/products/')
            })
        return Response({"error": "invalid username or password"}, status=400)
    
    @action(detail=False, methods=['get'], url_path='logout')
    def logout(self, request):
        logout(request)
        return Response({"message": "logout success"})

class ProductViewSet(viewsets.ModelViewSet):
    # TODO: add filter to get the product a PO owns
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return ProductCreationSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsProductOwner()]
        return [permissions.AllowAny()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ReportViewSet(viewsets.ModelViewSet):
    # TODO: add filter to get the reports a developer is assigned to
    queryset = Report.objects.all()
    serializer_class = ReportDetailSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), IsTester()]
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

    def retrieve(self, request, *args, **kwargs):
        # Excluded by project assumption: reflect changes immediately
        report = self.get_object()
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

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
    