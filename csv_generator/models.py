from django.db import models
from django.urls import reverse


class Schema(models.Model):

    SEPARATOR_CHOICES = (
        ("Comma", "Comma(,)"),
        ("Semicolon", "Semicolon(;)"),
        ("Tab", "Tab(/t)"),
        ("Space", "Space( )"),
        ("Pipe", "Pipe (|)"),
    )

    schema_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    column_separator = models.CharField(choices=SEPARATOR_CHOICES, max_length=30)
    last_modified = models.DateField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("schema_detail", kwargs={"schema_id": self.schema_id})

    def __str__(self):
        return self.name


class Column(models.Model):
    CHOICES = (
        ("Full Name", "Full Name"),
        ("Job", "Job"),
        ("Email", "Email"),
        ("Domain name", "Domain name"),
        ("Phone number", "Phone number"),
        ("Company name", "Company name"),
        ("Text", "Text"),
        ("Integer", "Integer"),
        ("Address", "Address"),
        ("Date", "Date"),
    )

    column_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    type = models.CharField(choices=CHOICES, max_length=30)

    from_range = models.IntegerField(blank=True, null=True)
    to_range = models.IntegerField(blank=True, null=True)

    order = models.IntegerField(blank=False, null=False)
    schema = models.ForeignKey(Schema, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class DataSet(models.Model):
    STATUS_CHOICES = (
        ("Ready", "Ready"),
        ("Processing", "Processing"),
    )

    dataset_id = models.AutoField(primary_key=True)
    schema = models.ForeignKey(Schema, on_delete=models.CASCADE)
    created = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    rows = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.schema.name} - {self.status}"
