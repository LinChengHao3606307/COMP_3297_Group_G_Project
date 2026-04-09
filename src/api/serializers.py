from rest_framework import serializers
from .models import *


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


class ProductSerializer(serializers.ModelSerializer):
    reports_url = serializers.HyperlinkedIdentityField(
        view_name='api:product-reports',
        read_only=True
    )

    class Meta:
        model = Product
        fields = ["id", "name", "version", "owner", "reports_url"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = UserSerializer(instance.owner).data
        return representation


class ReportSubmissionSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="name", queryset=Product.objects.all())
    url = serializers.HyperlinkedIdentityField(view_name='api:report-detail', lookup_field='pk', read_only=True)
    class Meta:
        model = Report
        fields = [
            "id", "created_at",
            "title", "description", "steps_to_reproduce", "email",
            "product", "url",
        ]
        read_only_fields = ["created_at"]


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['author'] = UserSerializer(instance.author).data
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

    # 2. The Comment Section
    comments = serializers.HyperlinkedIdentityField(view_name='api:report-comments', lookup_field='pk', read_only=True)
    comment_count = serializers.IntegerField(
        source='comments.count',
        read_only=True
    )

    # 3. Human-Readable Status
    status = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    url = serializers.HyperlinkedIdentityField(view_name='api:report-detail', lookup_field='pk', read_only=True)
    # actions = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "url", "title", "description", "status", "severity", "priority",
            "product", "assigned_to",
            "email", "comment_count", "comments",
            # "actions",
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