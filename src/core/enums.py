from django.db import models


class PropertyStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Свободен"
    RENTED = "RENTED", "В аренде"
    SUSPENDED = "SUSPENDED", "Пауза"
    ARCHIVED = "ARCHIVED", "Архив"


class PartyType(models.TextChoices):
    TENANT = "TENANT", "Арендатор"
    OWNER = "OWNER", "Собственник"
    STAFF = "STAFF", "Сотрудник"

class ContractStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    ACTIVE = "ACTIVE", "Активен"
    SUSPENDED = "SUSPENDED", "Приостановлен"
    TERMINATING = "TERMINATING", "Закрывается"
    CLOSED = "CLOSED", "Закрыт"
    CANCELLED = "CANCELLED", "Отменен"


class ObligationStatus(models.TextChoices):
    PLANNED = "PLANNED", "Запланировано"
    DUE = "DUE", "Срок сегодня"
    OVERDUE = "OVERDUE", "Просрочено"
    PARTIAL = "PARTIAL", "Частично оплачено"
    PAID_BY_TENANT = "PAID_BY_TENANT", "Оплачено арендатором"
    CLOSED = "CLOSED", "Закрыто"
    DISPUTED = "DISPUTED", "Спор"
    WRITTEN_OFF = "WRITTEN_OFF", "Списано"


class ReceiptAccountingStatus(models.TextChoices):
    # Внутренний статус передачи денег в бухгалтерию (НЕ про оплату арендатора)
    NOT_TRANSFERRED = "NOT_TRANSFERRED", "Не передано в бухгалтерию"
    TRANSFERRED = "TRANSFERRED", "Передано в бухгалтерию"
    ACCEPTED = "ACCEPTED", "Принято бухгалтерией"
