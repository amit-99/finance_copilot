import json
from datetime import datetime

class ChatEntry:
    def __init__(self, timestamp, sender, message, attachment=""):
        self.timestamp = timestamp
        self.sender = sender
        self.message = message
        self.attachment = attachment

    def to_dict(self):
        """Convert the ChatEntry instance to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "sender": self.sender,
            "message": self.message,
            "attachment": self.attachment
        }

    @classmethod
    def from_dict(cls, data):
        """Create a ChatEntry instance from a dictionary."""
        return cls(
            timestamp=data["timestamp"],
            sender=data["sender"],
            message=data["message"],
            attachment=data.get("attachment", "")
        )

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.message}"
