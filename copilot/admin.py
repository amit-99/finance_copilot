# admin.py

from django.contrib import admin

from copilot.models import Chat, Transaction, TransactionSummary, User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("userId", "familyId")

    list_display = ("userId", "name", "number")


class TransactionSummaryAdmin(admin.ModelAdmin):
    readonly_fields = ("formatted_data",)  # Make the data read-only

    list_display = ("familyId", "formatted_data")

    def formatted_data(self, obj):
        """Display the data in a readable JSON format."""
        return obj.data if isinstance(obj.data, dict) else obj.data.to_dict()

    # Exclude the raw 'data' field from form display if it's causing issues
    exclude = ("data",)


admin.site.register(User, UserAdmin)
admin.site.register(Transaction)
admin.site.register(TransactionSummary, TransactionSummaryAdmin)
admin.site.register(Chat)
