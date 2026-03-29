from django.db.models import Q
from rest_framework import serializers
from .models import *

role_to_code = {"productowner": "PO", "developer": "D", "tester": "T"}
code_to_role = {"PO": "Product Owner", "D": "Developer", "T": "Tester"}


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_id', 'role']

    def get_role(self, obj):
        return obj.get_role_display()


class ProductSerializer(serializers.ModelSerializer):
    # TODO: Modify this when adding view products methods
    class Meta:
        model = Product
        fields = '__all__'


class ReportSubmissionSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="name", queryset=Product.objects.all())
    owner = serializers.SlugRelatedField(slug_field="id", queryset=User.objects.filter(role='T'))
    class Meta:
        model = Report
        fields = [
            "id", "created_at",
            "title", "description", "steps_to_reproduce", "email",
            "product", "owner",
        ]
        read_only_fields = ["created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = UserSerializer(instance.owner).data
        return representation


class ReportEvaluationSerializer(serializers.ModelSerializer):
    EVALUATION_CHOICES = [
        (Report.Status.OPEN, "Open"),
        (Report.Status.REJECTED, "Rejected"),
    ]
    status = serializers.ChoiceField(choices=EVALUATION_CHOICES)


    class Meta:
        model = Report
        fields = [
            "status", "priority", "severity"
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = UserSerializer(instance.owner).data
        return representation

    def validate_status(self, value):
        if value not in [choice[0] for choice in self.EVALUATION_CHOICES]:
            raise serializers.ValidationError({"status": f'Invalid status value. Possible statuses: {[choice[1] for choice in self.EVALUATION_CHOICES]}'})
        return value


class ReportClaimSerializer(serializers.ModelSerializer):
    EVALUATION_CHOICES = [
        (Report.Status.ASSIGNED, "Assigned"),
    ]
    status = serializers.ChoiceField(choices=EVALUATION_CHOICES)
    developer = serializers.SlugRelatedField(slug_field="id", queryset=User.objects.filter(role='D'))

    class Meta:
        model = Report
        fields = [
            "status", "developer",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Handle the developer if one is assigned
        if instance.developer:
            representation['developer'] = UserSerializer(instance.developer).data
        else:
            representation['developer'] = None
        return representation

    def validate_status(self, value):
        if value not in [choice[0] for choice in self.EVALUATION_CHOICES]:
            raise serializers.ValidationError({"status": f'Invalid status value. Possible statuses: {[choice[1] for choice in self.EVALUATION_CHOICES]}'})
        return value


class CommentSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field="user_id", queryset=User.objects.filter(Q(role='PO') | Q(role='D')))

    class Meta:
        model = Comment
        fields = [
            "id", "text", "owner", "created_at", "owner"
        ]
        read_only_fields = ["created_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['owner'] = UserSerializer(instance.owner).data
        return representation
