from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.db import transaction

from core.models import LeaseContract, PaymentObligation
from core.enums import ObligationStatus


@dataclass(frozen=True)
class YearMonth:
    year: int
    month: int


def _add_months(ym: YearMonth, n: int) -> YearMonth:
    y, m = ym.year, ym.month
    m = m + n
    y = y + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return YearMonth(y, m)


def _first_due_ym(contract: LeaseContract) -> YearMonth:
    start = contract.start_date
    due_day = int(contract.due_day)
    due_this_month = date(start.year, start.month, due_day)

    if start <= due_this_month:
        return YearMonth(start.year, start.month)
    return _add_months(YearMonth(start.year, start.month), 1)


def ensure_obligations_window(contract: LeaseContract, months_ahead: int = 2) -> int:
    if months_ahead < 1:
        return 0

    first_ym = _first_due_ym(contract)
    target_yms = [_add_months(first_ym, i) for i in range(months_ahead)]

    existing = set(
        PaymentObligation.objects.filter(contract=contract)
        .values_list("period_year", "period_month")
    )

    responsible = contract.get_effective_responsible_user()

    created = 0
    with transaction.atomic():
        for ym in target_yms:
            key = (ym.year, ym.month)
            if key in existing:
                continue

            due_date = date(ym.year, ym.month, int(contract.due_day))

            PaymentObligation.objects.create(
                contract=contract,
                responsible_user=responsible,
                period_year=ym.year,
                period_month=ym.month,
                due_date=due_date,
                amount_due=contract.rent_amount,
                status=ObligationStatus.PLANNED,
                penalty_rule_snapshot=contract.penalty_rule or {},
                custom_fields={},
            )
            created += 1

    return created
