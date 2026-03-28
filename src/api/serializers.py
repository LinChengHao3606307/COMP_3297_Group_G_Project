from rest_framework import serializers, permissions
from .models import *

user_distinguisher = {"productowner":"PO", "developer": "D", "tester": "T"} 

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
    declared_role = serializers.CharField(write_only=True)
    declared_user_id = serializers.IntegerField(write_only=True)
    declared_report_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Comment
        fields = [
            "text","declared_role", "declared_report_id", "declared_user_id"
        ]

    def validate_declared_role(self, value):
        value = value.lower().replace(" ", "")
        if value != "productowner" and value != "developer":
            raise serializers.ValidationError("Comment is not submitted by product owner or developer!")
        return user_distinguisher[value]
