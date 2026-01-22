from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import LeaseContract
from core.enums import ContractStatus
from core.services.obligations import ensure_obligations_window


@receiver(post_save, sender=LeaseContract)
def on_contract_saved(sender, instance: LeaseContract, created: bool, **kwargs):
    if instance.status == ContractStatus.ACTIVE:
        ensure_obligations_window(instance, months_ahead=2)

from django.db.models.signals import post_delete
from core.models import PaymentReceipt


@receiver(post_save, sender=PaymentReceipt)
@receiver(post_delete, sender=PaymentReceipt)
def on_receipt_changed(sender, instance: PaymentReceipt, **kwargs):
    obligation = instance.obligation
    obligation.recompute_status()
    obligation.save(update_fields=["status"])
