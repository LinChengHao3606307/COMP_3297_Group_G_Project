from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    # Tester, Developer, Project Owner
    role = models.CharField(max_length=20, choices=(("T", "Tester"), ("D", "Developer"), ("PO", "Product Owner")))

    def __str__(self):
        return f"{self.get_role_display()} #{self.user_id}"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)

    def __str__(self):
        return f"Product #{self.id} {self.name} v{self.version} ({self.owner})"


class Report(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reports")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    developer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='claim_reports')

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


    status = models.TextField(choices=Status.choices, default=Status.NEW)
    priority = models.TextField(blank=True, choices=(
        ("Critical", "Critical"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")
    ))
    severity = models.TextField(blank=True, choices=(
        ("Critical", "Critical"), ("Major", "Major"), ("Minor", "Minor"), ("Low", "Low")
    ))
    title = models.TextField()
    description = models.TextField()
    steps_to_reproduce = models.TextField()
    email = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.id} ({self.product}, {self.owner})"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")

    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment #{self.id} ({self.report}, {self.owner})"