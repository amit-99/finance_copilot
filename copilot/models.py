from django.db import models

from copilot.datamodels.fields import YearlySummaryField
from copilot.datamodels.summary import YearlySummary

class User(models.Model):
    name = models.CharField(max_length=100)
    
    number = models.CharField(
        max_length=15,
        unique=True
    )
    
    familyId = models.CharField(max_length=50, blank=True, null=True)
    userId = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.name} ({self.number})"

class Expense(models.Model):
    EXPENSE_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    familyId = models.CharField(max_length=50)
    userId = models.CharField(max_length=50)
    type = models.CharField(max_length=7, choices=EXPENSE_TYPES)
    category = models.CharField(max_length=100)
    month = models.IntegerField()
    date = models.DateField()
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    recordType = models.CharField(max_length=20, default='expense')

    def __str__(self):
        return f"{self.type.capitalize()} - {self.category} ({self.date})"

class ExpenseSummary(models.Model):
    familyId = models.CharField(max_length=50)
    recordType = models.CharField(max_length=20, default='expensesummary')
    data = YearlySummaryField(default=YearlySummary)

    def save(self, *args, **kwargs):
        # Ensure the data is converted to a dictionary before saving
        if isinstance(self.data, YearlySummary):
            self.data = self.data.to_dict()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Summary for {self.familyId}: {self.data}"
