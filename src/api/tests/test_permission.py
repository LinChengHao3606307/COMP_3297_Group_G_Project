from django.test import RequestFactory
from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context, get_public_schema_name
from tenant_users.tenants.utils import create_public_tenant
from tenant_users.tenants.models import ExistsError

from api.permissions import (
    IsTester, IsDeveloper, IsProductOwner, 
    IsProjectMember, IsCommentAuthor, IsUserItself
)
from user_home.models import User
from api.models import Product, Report, Comment

class PermissionCoverageTests(TenantTestCase):

    @classmethod
    def setup_tenant(cls, tenant):
        try:
            create_public_tenant(domain_url="public.testserver", owner_email="pub@test.com")
        except ExistsError:
            pass
        
        with schema_context(get_public_schema_name()):
            owner, _ = User.objects.get_or_create(
                email="owner@test.com", 
                defaults={'role': User.Role.ADMIN}
            )
        tenant.owner = owner
        return tenant

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        
        # 1. Setup ALL users needed for coverage branches
        self.admin = User.objects.create(email="admin@test.com", role=User.Role.ADMIN)
        self.dev = User.objects.create(email="dev@test.com", role=User.Role.DEVELOPER)
        self.other_dev = User.objects.create(email="other_dev@test.com", role=User.Role.DEVELOPER)
        self.po = User.objects.create(email="po@test.com", role=User.Role.PRODUCT_OWNER)
        self.other_po = User.objects.create(email="other_po@test.com", role=User.Role.PRODUCT_OWNER)
        self.tester = User.objects.create(email="tester@test.com", role=User.Role.TESTER)

        # 2. Setup objects
        self.product = Product.objects.create(name="Project Alpha", owner=self.po)
        self.report = Report.objects.create(title="Bug A", product=self.product, assigned_to=self.dev)
        self.comment = Comment.objects.create(content="Fixing", report=self.report, author=self.dev)

    def _get_request(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_is_developer_full_coverage(self):
        perm = IsDeveloper()
        req_dev = self._get_request(self.dev)

        # Hitting line 16: Admin bypass
        self.assertTrue(perm.has_object_permission(self._get_request(self.admin), None, self.report))

        # Hitting line 18-19: Object is Report and assigned matches
        self.assertTrue(perm.has_object_permission(req_dev, None, self.report))

        # Hitting line 19 (False branch): Object is Report but wrong developer
        self.assertFalse(perm.has_object_permission(self._get_request(self.other_dev), None, self.report))

        # Hitting line 20: Object is Report but assigned_to is None
        with schema_context(self.tenant.schema_name):
            unassigned_report = Report.objects.create(title="None", product=self.product, assigned_to=None)
        self.assertTrue(perm.has_object_permission(req_dev, None, unassigned_report))

        # HITTING LINE 21: Object is NOT a Report (e.g., a Product)
        # This covers the final 'return True'
        self.assertTrue(perm.has_object_permission(req_dev, None, self.product))

    def test_is_product_owner_negatives(self):
        perm = IsProductOwner()
        req_other_po = self._get_request(self.other_po)

        # 1. Wrong PO for a Product (Line 33 -> 35 jump)
        self.assertFalse(perm.has_object_permission(req_other_po, None, self.product))

        # 2. Wrong PO for a Report (Line 31)
        self.assertFalse(perm.has_object_permission(req_other_po, None, self.report))

        # 3. Final 'return False' (Line 35): Pass an object that is neither Report nor Product
        self.assertFalse(perm.has_object_permission(req_other_po, None, self.comment))

    def test_is_comment_author_negatives(self):
        perm = IsCommentAuthor()
        # Hits line 45 (False branch: wrong author)
        self.assertFalse(perm.has_object_permission(self._get_request(self.other_dev), None, self.comment))
        # Hits final 'return False' (Line 47: wrong object type)
        self.assertFalse(perm.has_object_permission(self._get_request(self.dev), None, self.report))

    def test_is_user_itself_negatives(self):
        perm = IsUserItself()
        # Hits line 52 (False branch: wrong user)
        self.assertFalse(perm.has_object_permission(self._get_request(self.dev), None, self.tester))
        # Hits final 'return False' (Line 54: wrong object type)
        self.assertFalse(perm.has_object_permission(self._get_request(self.dev), None, self.product))

    def test_is_tester_global(self):
        perm = IsTester()
        self.assertTrue(perm.has_permission(self._get_request(self.tester), None))
        self.assertTrue(perm.has_permission(self._get_request(self.admin), None))
        self.assertFalse(perm.has_permission(self._get_request(self.dev), None))

    def test_is_project_member_global(self):
        perm = IsProjectMember()
        self.assertTrue(perm.has_permission(self._get_request(self.po), None))
        self.assertTrue(perm.has_permission(self._get_request(self.dev), None))
        self.assertFalse(perm.has_permission(self._get_request(self.tester), None))

    def test_admin_bypass_coverage(self):
        """
        EXPLICITLY covers the 'if request.user.is_admin: return True' line 
        for ALL permission classes.
        """
        admin_req = self._get_request(self.admin)
        
        # Test Global Permissions (has_permission)
        self.assertTrue(IsTester().has_permission(admin_req, None))
        self.assertTrue(IsProductOwner().has_permission(admin_req, None))
        self.assertTrue(IsProjectMember().has_permission(admin_req, None))
        # Note: IsDeveloper doesn't have an admin check in has_permission in your snippet, 
        # it just returns request.user.is_developer.

        # Test Object Permissions (has_object_permission)
        # These will all hit the 'if request.user.is_admin: return True' line and EXIT early.
        self.assertTrue(IsDeveloper().has_object_permission(admin_req, None, self.report))
        self.assertTrue(IsProductOwner().has_object_permission(admin_req, None, self.report))
        self.assertTrue(IsCommentAuthor().has_object_permission(admin_req, None, self.comment))
        self.assertTrue(IsUserItself().has_object_permission(admin_req, None, self.dev))

    def test_is_developer_remaining_branches(self):
        """Covers the rest of IsDeveloper."""
        perm = IsDeveloper()
        dev_req = self._get_request(self.dev)

        # Line 19: matches assigned dev
        self.assertTrue(perm.has_object_permission(dev_req, None, self.report))
        
        # Line 20: No one assigned
        self.report.assigned_to = None
        self.assertTrue(perm.has_object_permission(dev_req, None, self.report))

        # Line 21: Not a report (e.g. checking a Product)
        self.assertTrue(perm.has_object_permission(dev_req, None, self.product))

    def test_is_comment_author_branches(self):
        perm = IsCommentAuthor()
        # Author matches
        self.assertTrue(perm.has_object_permission(self._get_request(self.dev), None, self.comment))
        # Not a comment (hits final return False)
        self.assertFalse(perm.has_object_permission(self._get_request(self.dev), None, self.report))

    def test_is_user_itself_branches(self):
        perm = IsUserItself()
        # Self matches
        self.assertTrue(perm.has_object_permission(self._get_request(self.dev), None, self.dev))
        # Not a user object (hits final return False)
        self.assertFalse(perm.has_object_permission(self._get_request(self.dev), None, self.comment))