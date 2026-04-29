from django.test import RequestFactory
from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError
from rest_framework import serializers

from api.models import Product, Report, Comment
from user_home.models import User
from api.serializers import (
    UserRegistrationSerializer, 
    ReportUpdateSerializer, 
    DeveloperMetricsSerializer,
    CommentSerializer
)

class SerializerBranchCoverageTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(domain_url="public.testserver", owner_email="pub@test.com")
        except ExistsError:
            pass
        with schema_context(get_public_schema_name()):
            owner, _ = User.objects.get_or_create(email="owner@test.com", defaults={'role': User.Role.ADMIN})
        tenant.owner = owner
        return tenant

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.po = User.objects.create(email="po@test.com", role=User.Role.PRODUCT_OWNER)
        self.dev = User.objects.create(email="dev@test.com", role=User.Role.DEVELOPER)
        self.product = Product.objects.create(name="App", version="1.0", owner=self.po)

    def test_user_registration_serializer(self):
        """Covers create() and tenant logic in UserRegistrationSerializer."""
        request = self.factory.post('/')
        request.tenant = self.tenant
        data = {'email': 'new@test.com', 'password': 'Password123!', 'role': User.Role.DEVELOPER}
        
        serializer = UserRegistrationSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, 'new@test.com')
        # Verifies tenant association
        self.assertTrue(self.tenant.user_set.filter(email='new@test.com').exists())

    def test_developer_metrics_ratios(self):
        """Covers get_reopened_ratio branches."""
        serializer = DeveloperMetricsSerializer()
        
        # Branch: fixed_report <= 0 (Line 60)
        user_no_data = User(fixed_report=0, reopened_report=0)
        self.assertIsNone(serializer.get_reopened_ratio(user_no_data))
        
        # Branch: Valid ratio
        user_data = User(fixed_report=10, reopened_report=2)
        self.assertEqual(serializer.get_reopened_ratio(user_data), 0.2)

    def test_developer_effectiveness_branches(self):
        """Covers all effectiveness labels based on ratios."""
        serializer = DeveloperMetricsSerializer()
        
        # Insufficient data (fixed < 20)
        self.assertEqual(serializer.get_effectiveness(User(fixed_report=10)), "Insufficient data")
        
        # Good (< 0.03125)
        self.assertEqual(serializer.get_effectiveness(User(fixed_report=100, reopened_report=2)), "Good")
        
        # Fair (< 0.125)
        self.assertEqual(serializer.get_effectiveness(User(fixed_report=100, reopened_report=10)), "Fair")
        
        # Poor
        self.assertEqual(serializer.get_effectiveness(User(fixed_report=100, reopened_report=20)), "Poor")

    def test_report_update_status_transitions(self):
        """Covers get_allowed_statuses and to_internal_value validation."""
        report = Report.objects.create(product=self.product, status=Report.Status.NEW)
        
        # Test Invalid Transition (Line 191)
        serializer = ReportUpdateSerializer(instance=report, data={'status': Report.Status.FIXED})
        self.assertFalse(serializer.is_valid())
        self.assertIn("is not a valid choice", str(serializer.errors['status']))

    def test_report_update_duplicate_logic(self):
        """Covers Duplicate validation branches (Lines 205-215)."""
        report_new = Report.objects.create(product=self.product, status=Report.Status.NEW, title="R1")
        report_open = Report.objects.create(product=self.product, status=Report.Status.OPEN, title="R2")
        
        # 1. Missing duplicated_to
        serializer = ReportUpdateSerializer(instance=report_new, data={'status': Report.Status.DUPLICATE})
        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'status': Report.Status.DUPLICATE})

        # 2. Duplicate of itself
        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'status': Report.Status.DUPLICATE, 'duplicated_to': report_new})

        # 3. Duplicate of a NEW report
        report_new_2 = Report.objects.create(product=self.product, status=Report.Status.NEW, title="R3")
        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'status': Report.Status.DUPLICATE, 'duplicated_to': report_new_2})

    def test_report_update_open_validation(self):
        """Covers Priority/Severity requirement when moving to OPEN (Line 219)."""
        report = Report.objects.create(product=self.product, status=Report.Status.NEW)
        serializer = ReportUpdateSerializer(instance=report, data={'status': Report.Status.OPEN})
        
        # Should fail because priority/severity not provided in data
        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'status': Report.Status.OPEN})

    def test_report_update_read_only_enforcement(self):
        """Covers Line 229: once OPEN, priority/severity cannot be changed."""
        report = Report.objects.create(
            product=self.product, 
            status=Report.Status.OPEN, 
            priority=Report.Priority.HIGH, 
            severity=Report.Severity.MAJOR
        )
        serializer = ReportUpdateSerializer(instance=report, data={'priority': Report.Priority.LOW})
        
        # Even if passed in data, it should be ignored or raise error if it differs from instance
        with self.assertRaises(serializers.ValidationError):
            serializer.validate({'priority': Report.Priority.LOW, 'status': Report.Status.OPEN})

    def test_comment_serializer_author_branches(self):
        """Covers to_representation and author logic (Lines 279-282)."""
        report = Report.objects.create(product=self.product, title="Test Report")
        
        # Create a mock request to satisfy build_absolute_uri
        request = self.factory.get('/')
        
        # 1. Comment with Author
        comment_auth = Comment.objects.create(report=report, author=self.dev, content="Hi")
        # Pass the request in the context here!
        serializer = CommentSerializer(instance=comment_auth, context={'request': request})
        
        self.assertIsNotNone(serializer.data['author'])
        self.assertEqual(serializer.data['author']['email'], self.dev.email)
        
        # 2. Comment without Author (Anonymous)
        comment_anon = Comment.objects.create(report=report, author=None, content="Hi")
        # Pass the request in the context here too!
        serializer_anon = CommentSerializer(instance=comment_anon, context={'request': request})
        
        self.assertIsNone(serializer_anon.data['author'])

    def test_report_update_severity_provided(self):
        """
        Covers the branch where severity IS provided for a NEW report.
        This makes 'if not data.get("severity")' evaluate to False.
        """
        report = Report.objects.create(
            product=self.product, 
            status=Report.Status.NEW
        )
        
        # Ensure we use attributes that actually exist in your model
        # Using MAJOR as it is standard, change to whatever your model uses.
        data = {
            "status": Report.Status.OPEN,
            "priority": Report.Priority.HIGH, 
            "severity": Report.Severity.MAJOR 
        }
        
        serializer = ReportUpdateSerializer(instance=report, data=data)
        
        # This will trigger validate(). 
        # Since status is NEW and we PROVIDED severity, 
        # the 'if not data.get("severity")' branch is skipped.
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_comment_author_method_coverage(self):
        """
        Explicitly covers the get_author(self, obj) method branches.
        """
        report = Report.objects.create(product=self.product, title="Coverage Report")
        request = self.factory.get('/')
        
        # 1. Branch: if obj.author is True (Line 272-273)
        comment_with_author = Comment.objects.create(
            report=report, 
            author=self.dev, 
            content="Has author"
        )
        serializer1 = CommentSerializer(instance=comment_with_author, context={'request': request})
        # Accessing .data calls to_representation, which calls get_author via the field
        author_data = serializer1.get_author(comment_with_author)
        self.assertEqual(author_data['email'], self.dev.email)

        # 2. Branch: if obj.author is False/None (Line 274)
        comment_no_author = Comment.objects.create(
            report=report, 
            author=None, 
            content="No author"
        )
        serializer2 = CommentSerializer(instance=comment_no_author, context={'request': request})
        author_data_none = serializer2.get_author(comment_no_author)
        self.assertIsNone(author_data_none)