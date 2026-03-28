from rest_framework import serializers, permissions
from .models import *

role_to_code = {"productowner": "PO", "developer": "D", "tester": "T"}
code_to_role = {"PO": "Product Owner", "D": "Developer", "T": "Tester"}

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    declared_role = serializers.CharField(write_only=True)
    declared_user_id = serializers.IntegerField(write_only=True)
    declared_product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Report
        fields = [
            "title", "description", "steps_to_reproduce", "email",
            "declared_role", "declared_user_id", "declared_product_id"
        ]

    def validate_declared_role(self, value):
        if value.lower() != "tester":
            raise serializers.ValidationError("Report submitter is not a tester")
        return role_to_code[value.lower()]


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_id', 'role']

    def get_role(self, obj):
        return obj.get_role_display()


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
