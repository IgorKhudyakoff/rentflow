from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import LeaseContract
from core.enums import ContractStatus
from core.services.obligations import ensure_obligations_window


@receiver(post_save, sender=LeaseContract)
def on_contract_saved(sender, instance: LeaseContract, created: bool, **kwargs):
    if instance.status == ContractStatus.ACTIVE:
        ensure_obligations_window(instance, months_ahead=2)
