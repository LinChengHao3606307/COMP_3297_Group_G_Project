from rest_framework import serializers, permissions
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


class ReportSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="name", queryset=Product.objects.all())
    owner = serializers.SlugRelatedField(slug_field="user_id", queryset=User.objects.filter(role='T'))

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


class CommentSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    declared_role = serializers.CharField(write_only=True)
    declared_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = [
            "id", "text", "owner", "created_at",
            "declared_role", "declared_user_id",
        ]
        read_only_fields = ["created_at"]

    def validate_declared_role(self, value):
        value = value.lower().replace(" ", "")
        if value != "productowner" and value != "developer":
            raise serializers.ValidationError("Comment is not submitted by product owner or developer!")
        return role_to_code[value]
