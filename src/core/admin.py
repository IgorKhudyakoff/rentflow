from django.contrib import admin
from .models import Property, Party, LeaseContract, PaymentObligation


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "responsible_user", "address", "updated_at")
    list_filter = ("status", "responsible_user")
    search_fields = ("name", "address")


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "party_type", "phone", "email", "updated_at")
    list_filter = ("party_type",)
    search_fields = ("name", "phone", "email")


@admin.register(LeaseContract)
class LeaseContractAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "tenant", "status", "responsible_user", "start_date", "end_date", "rent_amount", "due_day")
    list_filter = ("status", "responsible_user")
    search_fields = ("property__name", "tenant__name")


@admin.register(PaymentObligation)
class PaymentObligationAdmin(admin.ModelAdmin):
    list_display = ("id", "contract", "period_month", "period_year", "due_date", "amount_due", "status", "responsible_user", "updated_at")
    list_filter = ("status", "period_year", "period_month", "responsible_user")
    search_fields = ("contract__property__name", "contract__tenant__name")
