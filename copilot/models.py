import uuid

from django.db import models

from copilot.datamodels.chatentry import ChatEntry
from copilot.datamodels.fields import YearlySummaryField
from copilot.datamodels.summary import YearlySummary


class User(models.Model):
    name = models.CharField(max_length=100)

    number = models.CharField(max_length=15, unique=True)

    userId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    familyId = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.familyId = self.userId
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.number})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    familyId = models.CharField(max_length=50)
    userId = models.CharField(max_length=50)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=100)
    year = models.IntegerField(null=True)
    month = models.IntegerField(blank=True, null=True)
    day = models.IntegerField(blank=True, null=True)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    recordType = models.CharField(max_length=20, default="transaction")

    def __str__(self):
        return f"{self.type.capitalize()} - {self.category}"


class TransactionSummary(models.Model):
    familyId = models.CharField(max_length=50)
    recordType = models.CharField(max_length=20, default="transactionsummary")
    data = YearlySummaryField(default=YearlySummary)

    def save(self, *args, **kwargs):
        # Ensure the data is converted to a dictionary before saving
        if isinstance(self.data, YearlySummary):
            self.data = self.data.to_dict()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Summary for {self.familyId}: {self.data}"


class Chat(models.Model):
    userId = models.CharField(max_length=50)
    # Store data as a list of dictionaries
    data = models.JSONField(default=list)

    def __str__(self):
        return f"Chat for {self.userId}: {self.data}"

    def get_chat_entries(self):
        """Convert the stored data to a list of ChatEntry objects."""
        return [ChatEntry.from_dict(entry) for entry in self.data]

    def add_chat_entry(self, entry):
        """Add a ChatEntry to the 'data' field."""
        if isinstance(entry, ChatEntry):
            self.data.append(entry.to_dict())
        else:
            raise ValueError("entry must be a ChatEntry instance")

    def save(self, *args, **kwargs):
        # Clean and save chat data as a list of dictionaries
        super().save(*args, **kwargs)


# class Metadata(models.Model):
