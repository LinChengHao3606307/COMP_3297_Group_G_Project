from rest_framework import serializers
from .models import *
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

status_transitions = {
    Report.Status.NEW: [Report.Status.OPEN, Report.Status.REJECTED, Report.Status.DUPLICATE],
    Report.Status.OPEN: [Report.Status.ASSIGNED],
    Report.Status.ASSIGNED: [Report.Status.FIXED, Report.Status.CANNOT_REPRODUCE],
    Report.Status.FIXED: [Report.Status.RESOLVED, Report.Status.REOPENED],
    Report.Status.REOPENED: [Report.Status.ASSIGNED],
}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {"password": {"write_only": True}}

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=['tester', 'developer', 'product_owner'], required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        username = validated_data['username']
        email = validated_data.get('email', '')
        password = validated_data['password']

        if role == 'developer':
            user = Developer.objects.create_user(
                username=username,
                email=email,
                password=password
            )
        elif role == 'product_owner':
            user = ProductOwner.objects.create_user(
                username=username,
                email=email,
                password=password
            )
        elif role == 'tester':
            user = Tester.objects.create_user(
                username=username,
                email=email,
                password=password
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
        return user

class ProductDetailSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    reports = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(source='reports.count', read_only=True)

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.id}')
        return None
    
    def get_reports(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.id}/report/')
        return None
    
    class Meta:
        model = Product
        fields = ["url", "id", "name", "version", "owner", "reports", "comment_count"]

class ProductCreationSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field="username", queryset=ProductOwner.objects.all())

    class Meta:
        model = Product
        fields = [
            "owner",
            "name",
            "version",
        ]

class ReportDetailSerializer(serializers.ModelSerializer):
    # 1. Nested Details
    product = serializers.CharField(source='product.name')  # Simple name
    assigned_to = UserSerializer(read_only=True)

    comments = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(
        source='comments.count',
        read_only=True
    )

    # 3. Human-Readable Status
    status = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.id}/')
        return None

    def get_comments(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.id}/comments/')
        return None

    class Meta:
        model = Report
        fields = [
            "url", "id", "title", "description", "status", "severity", "priority",
            "product", "assigned_to",
            "email", "comment_count", "comments",
        ]

class ReportSubmissionSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="name", queryset=Product.objects.all())
    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.id}/')
        return None
    class Meta:
        model = Report
        fields = [
            "url", "id", "product", "created_at",
            "title", "description", "steps_to_reproduce",  
            "email"
        ]
        read_only_fields = ["created_at"]


class ReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ["title", "description", "steps_to_reproduce", "email", "created_at"]

    def __init__(self, *args, **kwargs):
        super(ReportUpdateSerializer, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields["status"].choices = self.get_allowed_statuses()

    def to_internal_value(self, data):
        status_input = data.get('status')
        valid_choices = self.get_allowed_statuses()

        if status_input and status_input not in valid_choices:
            raise serializers.ValidationError({
                "status": f"'{status_input}' is not a valid choice. Available options: {', '.join(valid_choices)}"
            })

        return super().to_internal_value(data)

    def get_allowed_statuses(self):
        current_status = self.instance.status
        allowed_new_status = status_transitions.get(current_status, [])
        return [current_status] + allowed_new_status




    # Legacy code. Combined to update()
    # def get_actions(self, obj):
    #     request = self.context.get('request')
    #     links = {}
    #     if obj.status == Report.Status.NEW:
    #         links['evaluate'] = reverse('api:report-evaluate', kwargs={'pk': obj.pk}, request=request)
    #
    #     if obj.status == Report.Status.OPEN:
    #         links['claim'] = reverse('api:report-claim', kwargs={'pk': obj.pk}, request=request)
    #
    #     if obj.status == Report.Status.ASSIGNED:
    #         links['submit_fix'] = reverse('api:report-fix', kwargs={'pk': obj.pk}, request=request)
    #
    #     if obj.status == Report.Status.FIXED:
    #         links['resolve'] = reverse('api:report-resolve', kwargs={'pk': obj.pk}, request=request)
    #
    #     return links

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.report.product.id}/report/{obj.report.id}/comments/{obj.id}')
        return None
    
    class Meta:
        model = Comment
        fields = [
            "url", "id", "content", "author", "created_at"
        ]
        read_only_fields = ["created_at"]

    def get_author(self, obj):
        if obj.author:
            return UserSerializer(obj.author).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.author:
            representation['author'] = UserSerializer(instance.author).data
        else:
            representation['author'] = None
        return representation
