from rest_framework import serializers
from .models import *
from django.contrib.auth.password_validation import validate_password

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


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        from django.contrib.auth import authenticate
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        data['user'] = user
        return data


class ProductSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api:products-detail',
        read_only=True
    )
    owner = serializers.SlugRelatedField(slug_field='username', queryset=ProductOwner.objects.all())
    
    class Meta:
        model = Product
        fields = ["url", "id", "name", "version", "owner"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = UserSerializer(instance.owner).data
        return representation


class ReportSubmissionSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="name", queryset=Product.objects.all())
    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product_id}/report/{obj.pk}/')
        return None
    class Meta:
        model = Report
        fields = [
            "product", "id", "created_at",
            "title", "description", "steps_to_reproduce",  
            "email", "url",
        ]
        read_only_fields = ["created_at"]

class ProductCreationSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field="username", queryset=ProductOwner.objects.all())

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product_id}/report/{obj.pk}/')
        return None
    class Meta:
        model = Product
        fields = [
            "owner",
            "name",
            "version",
        ]
    
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = [
            "id", "content", "author", "created_at"
        ]
        read_only_fields = ["created_at"]

    def get_author(self, obj):
        if obj.author:
            return UserSerializer(obj.author).data
        return None

    def create(self, validated_data):
        # Convert AnonymousUser to null so the DB stores anonymous comments as author=None
        author = validated_data.get('author', None)
        if author is not None and getattr(author, 'is_anonymous', False):
            validated_data['author'] = None
        return super().create(validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.author:
            representation['author'] = UserSerializer(instance.author).data
        else:
            representation['author'] = None
        return representation

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
            return request.build_absolute_uri(f'/products/{obj.product_id}/report/{obj.pk}/')
        return None

    def get_comments(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product_id}/report/{obj.pk}/comments/')
        return None

    class Meta:
        model = Report
        fields = [
            "id", "url", "title", "description", "status", "severity", "priority",
            "product", "assigned_to",
            "email", "comment_count", "comments",
        ]

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


class ReportListSerializer(serializers.ModelSerializer):

    status = serializers.CharField(source='get_status_display', read_only=True)
    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product_id}/report/{obj.pk}/')
        return None
    
    class Meta:
        model = Report
        fields = ["id", "url", "title", "status"]


class ProductDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    reports = serializers.SerializerMethodField()
    comment_count = serializers.IntegerField(source='reports.count', read_only=True)

    def get_reports(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.id}/report/')
        return None
    
    class Meta:
        model = Product
        fields = ["id", "name", "version", "owner", "reports", "comment_count"]

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