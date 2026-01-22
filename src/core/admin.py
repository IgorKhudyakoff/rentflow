from django.contrib import admin
from .models import Property, Party, LeaseContract, PaymentObligation, PaymentReceipt


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
    list_display = (
        "id",
        "property",
        "tenant",
        "status",
        "responsible_user",
        "start_date",
        "end_date",
        "rent_amount",
        "due_day",
    )
    list_filter = ("status", "responsible_user")
    search_fields = ("property__name", "tenant__name")


class PaymentReceiptInline(admin.TabularInline):
    model = PaymentReceipt
    extra = 0
    fields = ("amount_received", "received_by", "comment", "received_at")
    readonly_fields = ("received_at",)
    autocomplete_fields = ("received_by",)
    ordering = ("-received_at",)

    def get_formset(self, request, obj=None, **kwargs):
        """
        Pre-fill received_by with current user for new inline rows.
        Still editable (e.g., for superusers correcting history).
        """
        formset = super().get_formset(request, obj, **kwargs)
        try:
            form = formset.form
            if "received_by" in form.base_fields:
                form.base_fields["received_by"].initial = request.user.pk
        except Exception:
            pass
        return formset


@admin.register(PaymentObligation)
class PaymentObligationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contract",
        "period_month",
        "period_year",
        "due_date",
        "amount_due",
        "status",
        "responsible_user",
        "updated_at",
    )
    list_filter = ("status", "period_year", "period_month", "responsible_user")
    search_fields = ("contract__property__name", "contract__tenant__name")
    inlines = (PaymentReceiptInline,)

    def get_inline_instances(self, request, obj=None):
        # Показываем inline с фактами денег
        # ТОЛЬКО при редактировании существующего обязательства
        # На форме создания (obj=None) inline скрыт
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def save_formset(self, request, form, formset, change):
        # Автоматически проставляем received_by текущим пользователем,
        # если для новых Receipt он не выбран вручную.
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, PaymentReceipt) and not obj.received_by_id:
                obj.received_by = request.user
            obj.save()
        formset.save_m2m()


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "obligation",
        "amount_received",
        "received_by",
        "received_at",
    )
    list_filter = ("received_by",)
    search_fields = (
        "obligation__contract__property__name",
        "obligation__contract__tenant__name",
    )
    autocomplete_fields = ("obligation", "received_by")
