from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    # Tester, Developer, Project Owner
    role = models.CharField(max_length=20, choices=(("T", "Tester"), ("D", "Developer"), ("PO", "Project Owner")))

    def __str__(self):
        return f"{self.role} #{self.user_id}"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)

    def __str__(self):
        return f"Product #{self.id} {self.name} v{self.version} ({self.owner})"


class Report(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # New, Open, Assigned, Fixed, Resolved, Reopened, Rejected, Duplicate, Cannot reproduce
    status = models.TextField(choices=(
        ("New", "New"), ("Open", "Open"), ("Assigned", "Assigned"), ("Fixed", "Fixed"), ("Resolved", "Resolved"),
        ("Reopened", "Reopened"), ("Rejected", "Rejected"), ("Duplicate", "Duplicate"), ("Cannot reproduce", "Cannot reproduce"),
    ))
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

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.id} ({self.product}, {self.owner})"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    text = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment #{self.id} ({self.report}, {self.owner})"