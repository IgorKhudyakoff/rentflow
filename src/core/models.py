from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

from .enums import (
    PropertyStatus,
    PartyType,
    ContractStatus,
    ObligationStatus,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        abstract = True


class Property(TimeStampedModel):
    name = models.CharField("Название/метка", max_length=255)
    address = models.CharField("Адрес", max_length=500, blank=True, default="")
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=PropertyStatus.choices,
        default=PropertyStatus.AVAILABLE,
    )

    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Ответственный (по объекту)",
        related_name="properties_responsible",
    )

    custom_fields = models.JSONField("Доп. поля", default=dict, blank=True)

    class Meta:
        verbose_name = "Объект недвижимости"
        verbose_name_plural = "Объекты недвижимости"

    def __str__(self) -> str:
        return self.name


class Party(TimeStampedModel):
    party_type = models.CharField(
        "Тип",
        max_length=10,
        choices=PartyType.choices,
        default=PartyType.TENANT,
    )
    name = models.CharField("ФИО / Название", max_length=255)
    phone = models.CharField("Телефон", max_length=50, blank=True, default="")
    email = models.EmailField("Email", blank=True, default="")
    notes = models.TextField("Примечания", blank=True, default="")
    custom_fields = models.JSONField("Доп. поля", default=dict, blank=True)

    class Meta:
        verbose_name = "Контрагент"
        verbose_name_plural = "Контрагенты"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_party_type_display()})"


class LeaseContract(TimeStampedModel):
    property = models.ForeignKey(Property, on_delete=models.PROTECT, verbose_name="Объект")
    tenant = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        verbose_name="Арендатор",
        related_name="lease_contracts",
    )

    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Ответственный (по договору)",
        related_name="contracts_responsible",
        help_text="Если не задан, будет использоваться ответственный по объекту.",
    )

    status = models.CharField(
        "Статус договора",
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT,
    )

    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания", null=True, blank=True)

    rent_amount = models.DecimalField(
        "Ставка аренды (в месяц)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    due_day = models.PositiveSmallIntegerField(
        "День оплаты (1-28)",
        default=1,
        help_text="Лучше 1-28, чтобы не ломаться на феврале.",
        validators=[MinValueValidator(1)],
    )

    deposit_amount = models.DecimalField(
        "Обеспечительный платеж (депозит)",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    penalty_rule = models.JSONField(
        "Правило пени (конфиг)",
        default=dict,
        blank=True,
        help_text="Пока просто JSON. Позже формализуем.",
    )

    custom_fields = models.JSONField("Доп. поля", default=dict, blank=True)

    class Meta:
        verbose_name = "Договор аренды"
        verbose_name_plural = "Договоры аренды"

    def __str__(self) -> str:
        return f"Договор #{self.id} — {self.property} — {self.tenant}"

    def get_effective_responsible_user(self):
        return self.responsible_user or self.property.responsible_user


class PaymentObligation(TimeStampedModel):
    contract = models.ForeignKey(
        LeaseContract,
        on_delete=models.PROTECT,
        verbose_name="Договор",
        related_name="obligations",
    )

    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Ответственный (снапшот)",
        related_name="obligations_responsible",
        help_text="Фиксируется при создании обязательства.",
    )

    period_year = models.PositiveSmallIntegerField("Год")
    period_month = models.PositiveSmallIntegerField("Месяц")

    due_date = models.DateField("Срок оплаты")
    amount_due = models.DecimalField(
        "К оплате",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    status = models.CharField(
        "Статус",
        max_length=20,
        choices=ObligationStatus.choices,
        default=ObligationStatus.PLANNED,
    )

    penalty_rule_snapshot = models.JSONField(
        "Снапшот правила пени",
        default=dict,
        blank=True,
        help_text="Фиксация правила на момент создания обязательства.",
    )

    custom_fields = models.JSONField("Доп. поля", default=dict, blank=True)

    class Meta:
        verbose_name = "Обязательство по оплате"
        verbose_name_plural = "Обязательства по оплате"
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "period_year", "period_month"],
                name="uniq_contract_period",
            )
        ]

    def __str__(self) -> str:
        return f"{self.contract} — {self.period_month:02d}.{self.period_year} — {self.amount_due}"

    def recompute_status(self, today: date | None = None) -> None:
        today = today or date.today()
        if self.status in {ObligationStatus.CLOSED, ObligationStatus.PAID_BY_TENANT, ObligationStatus.WRITTEN_OFF}:
            return

        if today < self.due_date:
            self.status = ObligationStatus.PLANNED
        elif today == self.due_date:
            self.status = ObligationStatus.DUE
        else:
            self.status = ObligationStatus.OVERDUE
        self.save(update_fields=["status"])
