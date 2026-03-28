from rest_framework import serializers, permissions
from .models import *


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
        return "T"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'role']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
