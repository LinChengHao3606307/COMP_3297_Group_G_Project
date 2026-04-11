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

    def get_serializer_class(self):
        print(self.action)
        if self.action == "create":
            print("*"*10)
            return ProductCreationSerializer
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsProductOwner()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get', 'post'], url_path='create')
    def create_product(self, request):
        return self.create(request)
    
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
        if self.action in ["evaluate", "resolve"]:
            return [permissions.IsAuthenticated(), IsProductOwner()]
        elif self.action in ["claim", "fix"]:
            return [permissions.IsAuthenticated(), IsDeveloper()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            print("="*10)
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

    def retrieve(self, request, *args, **kwargs):
        # Excluded by project assumption: reflect changes immediately
        report = self.get_object()
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["GET", "POST"], url_path="comments")
    def comments(self, request, pk=None, *args, **kwargs):
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

from django.contrib.auth import authenticate, login, logout
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action in ["create", "login"]:
            return LoginSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        print(self.action)
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        email = serializer.validated_data.get('email', '')

        user = User.objects.create_user(username=username, email=email, password=password)
        out = UserSerializer(user)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get', 'post'], url_path='login')
    def login(self, request):
        if request.method == 'GET':
            return Response({"message": "please login vis POST"}, status=405)
        
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
        return Response({"message": "logout success"}, status=status.HTTP_200_OK)
    