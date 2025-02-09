# models/fields.py
from django.db.models import JSONField
from .summary import YearlySummary

class YearlySummaryField(JSONField):
    description = "Stores YearlySummary as JSON"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return YearlySummary()
        return YearlySummary.from_dict(value)

    def to_python(self, value):
        if isinstance(value, YearlySummary):
            return value
        if isinstance(value, dict):
            return YearlySummary.from_dict(value)
        return YearlySummary()

    def get_prep_value(self, value):
        if isinstance(value, YearlySummary):
            return value.to_dict()
        return super().get_prep_value(value)
