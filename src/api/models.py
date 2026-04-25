from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # Excluded by project assumption: support Tester registration
    pass


class Developer(User):
    class Meta:
        verbose_name = "Developer"
        verbose_name_plural = "Developers"

    def __str__(self):
        return f"Developer '{self.username}'"


class ProductOwner(User):
    class Meta:
        verbose_name = "Product Owner"
        verbose_name_plural = "Product Owners"

    def __str__(self):
        return f"Product Owner '{self.username}'"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(ProductOwner, on_delete=models.CASCADE, related_name="product")

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)

    def __str__(self):
        return f"Product '{self.name} v{self.version}' ({self.owner})"


class Report(models.Model):
    # TODO: add foreignkey `parent` to link duplicate reports
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reports")
    assigned_to = models.ForeignKey(Developer, on_delete=models.SET_NULL, null=True, blank=True, related_name='report')
    duplicated_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')
    # New, Open, Assigned, Fixed, Resolved, Reopened, Rejected, Duplicate, Cannot reproduce
    class Status(models.TextChoices):
        # Submission
        NEW = "New", "New"

        # Evaluation
        OPEN = "Open", "Open"
        REJECTED = "Rejected", "Rejected"

        # Development
        ASSIGNED = "Assigned", "Assigned"
        FIXED = "Fixed", "Fixed"

        # Resolution
        RESOLVED = "Resolved", "Resolved"

        # To be implemented
        REOPENED = "Reopened", "Reopened"
        DUPLICATE = "Duplicate", "Duplicate"
        CANNOT_REPRODUCE = "Cannot Reproduce", "Cannot Reproduce"

    class Priority(models.TextChoices):
        CRITICAL = "Critical", "Critical"
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    class Severity(models.TextChoices):
        CRITICAL = "Critical", "Critical"
        MAJOR = "Major", "Major"
        MINOR = "Minor", "Minor"
        LOW = "Low", "Low"

    status = models.TextField(choices=Status.choices, default=Status.NEW)
    priority = models.TextField(blank=True, choices=Priority.choices)
    severity = models.TextField(blank=True, choices=Severity.choices)
    title = models.TextField()
    description = models.TextField()
    steps_to_reproduce = models.TextField()
    email = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report '{self.title}' ({self.product})"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment #{self.id} ({self.author} at {self.created_at} on {self.report})"