from rest_framework import serializers
from .models import *
from user_home.models import User
from django.contrib.auth.password_validation import validate_password
from django_tenants.utils import schema_context, get_public_schema_name, get_tenant

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
        fields = ['id', 'email', 'password']
        extra_kwargs = {"password": {"write_only": True}}

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=[User.Role.PRODUCT_OWNER, User.Role.DEVELOPER, User.Role.TESTER], required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'role']

    def create(self, validated_data):

        request = self.context.get('request')
        current_tenant = get_tenant(request)

        role = validated_data.pop('role')
        email = validated_data.get('email', '')
        password = validated_data['password']
        with schema_context(get_public_schema_name()):
            user = User.objects.create_user(
                email=email, password=password, role=role
            )

        current_tenant.add_user(user)
        user.save()

        return user

class DeveloperMetricsSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    effectiveness = serializers.SerializerMethodField()
    fixed_report = serializers.IntegerField(read_only=True)
    reopened_report = serializers.IntegerField(read_only=True)
    reopened_ratio = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['url', 'id', 'email', 'fixed_report', 'reopened_report', 'reopened_ratio', 'effectiveness']

    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/developer-metrics/{obj.id}/')
        return None

    def get_reopened_ratio(self, obj):
        if obj.fixed_report <= 0:
            return None
        return round(obj.reopened_report / obj.fixed_report, 4)

    def get_effectiveness(self, obj):
        fixed = obj.fixed_report
        reopened = obj.reopened_report

        if fixed < 20:
            return "Insufficient data"

        ratio = reopened / fixed
        if ratio < 0.03125:
            return "Good"
        elif ratio < 0.125:
            return "Fair"
        else:
            return "Poor"

class ProductDetailSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    reports = serializers.SerializerMethodField()
    report_count = serializers.IntegerField(source='reports.count', read_only=True)

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
        fields = ["url", "id", "name", "version", "owner", "reports", "report_count"]

class ProductCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "owner",
            "name",
            "version",
            "id",
        ]
        extra_kwargs = {
            'owner': {'read_only': True}
        }

class ReportDetailSerializer(serializers.ModelSerializer):
    # 1. Nested Details
    product = serializers.CharField(source='product.name')  # Simple name
    assigned_to = UserSerializer(read_only=True)

    comments = serializers.SerializerMethodField()
    def get_comments(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.id}/comments/')
        return None
    
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
    
    duplicated_to = serializers.SerializerMethodField()
    def get_duplicated_to(self, obj):
        if obj.duplicated_to:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.duplicated_to.id}/')
        return None

    class Meta:
        model = Report
        fields = [
            "url", "id", "title", "description", "status", "severity", "priority",
            "product", "assigned_to",
            "email", "comment_count", "comments",
            "duplicated_to", "updated_at"
        ]

class ReportSubmissionSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/products/{obj.product.id}/report/{obj.id}/')
        return None
    class Meta:
        model = Report
        fields = [
            "url", "id", "created_at",
            "title", "description", "steps_to_reproduce",  
            "email", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class ReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["status", "priority", "severity", "duplicated_to"]
        read_only_fields = ["title", "description", "product", "steps_to_reproduce", "email", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super(ReportUpdateSerializer, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["status"].choices = self.get_allowed_statuses()
            if self.instance.status != Report.Status.NEW:
                #remove priotiy and severity from required fields and make them read-only (not show in gui)
                self.fields['priority'].required = False
                self.fields['severity'].required = False
                self.fields['duplicated_to'].required = False
                self.fields['priority'].read_only = True
                self.fields['severity'].read_only = True
                self.fields['duplicated_to'].read_only = True
            if self.instance.status == Report.Status.DUPLICATE:
                self.fields['duplicated_to'].required = True
                self.fields['duplicated_to'].read_only = False

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
    
    def validate(self, data):
        instance = self.instance
        if instance.status == Report.Status.NEW:
            if data.get("status") == Report.Status.DUPLICATE:
                duplicate_report = data.get("duplicated_to")
                if not duplicate_report:
                    raise serializers.ValidationError("This field is required when changing status to DUPLICATE.")
                if duplicate_report == instance:
                    raise serializers.ValidationError("A report cannot be marked as duplicate of itself.")
                if duplicate_report.status == Report.Status.NEW:
                    raise serializers.ValidationError("Cannot mark as duplicate of a report that is still NEW.")
            elif (not data.get("priority") or not data.get("severity")) and data.get("status") == Report.Status.OPEN:
                raise serializers.ValidationError(
                    "Priority and severity must be set when report is NEW"
                )
        else:
            if not data.get("priority"):
                data["priority"] = instance.priority
            if not data.get("severity"):
                data["severity"] = instance.severity

            if data.get("priority") != instance.priority or data.get("severity") != instance.severity:
                raise serializers.ValidationError(
                    "Priority and severity cannot be changed once the report is OPEN"
                )
        return data
    




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
