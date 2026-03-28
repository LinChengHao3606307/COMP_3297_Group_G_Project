from django.db import models


class User(models.Model):
    _id = models.AutoField(primary_key=True)
    person_id = models.IntegerField()
    # Tester, Developer, Project Owner
    role = models.CharField(max_length=20, choices=(("T", "Tester"), ("D", "Developer"), ("PO", "Project Owner")))


class Product(models.Model):
    title = models.CharField(max_length=100)
    _id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    version = models.CharField(max_length=20)


class Report(models.Model):
    _id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # New, Open, Assigned, Fixed, Resolved, Reopened, Rejected, Duplicate, Cannot reproduce
    status = models.TextField(choices=(
        ("New", "New"), ("Open", "Open"), ("Assigned", "Assigned"), ("Fixed", "Fixed"), ("Resolved", "Resolved"),
        ("Reopened", "Reopened"), ("Rejected", "Rejected"), ("Duplicate", "Duplicate"), ("Cannot reproduce", "Cannot reproduce"),
    ))
    priority = models.TextField(choices=(
        ("Critical", "Critical"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")
    ))
    severity = models.TextField(choices=(
        ("Critical", "Critical"), ("Major", "Major"), ("Minor", "Minor"), ("Low", "Low")
    ))
    title = models.TextField()
    description = models.TextField()
    steps_to_reproduce = models.TextField()
    email = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    _id = models.AutoField(primary_key=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    text = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)