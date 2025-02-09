# models/summary.py

class MonthlySummary:
    def __init__(self, income=0, expense=0):
        self.income = income
        self.expense = expense

    def to_dict(self):
        return {
            'income': self.income,
            'expense': self.expense
        }

    @classmethod
    def from_dict(cls, data):
        return cls(income=data.get('income', 0), expense=data.get('expense', 0))


class YearlySummary:
    def __init__(self):
        self.years = {}  # {year: {month: MonthlySummary}}

    def add_monthly_summary(self, year, month, income=0, expense=0):
        if year not in self.years:
            self.years[year] = {}
        self.years[year][month] = MonthlySummary(income, expense)

    def to_dict(self):
        """Convert to a JSON-serializable dictionary."""
        return {
            year: {month: summary.to_dict() for month, summary in months.items()}
            for year, months in self.years.items()
        }

    @classmethod
    def from_dict(cls, data):
        """Convert from a dictionary to a YearlySummary instance."""
        instance = cls()
        for year, months in data.items():
            for month, summary in months.items():
                instance.add_monthly_summary(year, month, summary.get('income', 0), summary.get('expense', 0))
        return instance
