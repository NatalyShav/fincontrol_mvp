from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    telegram_linked = models.BooleanField(default=False)
    send_daily_report = models.BooleanField(default=True)
    send_weekly_report = models.BooleanField(default=True)

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_income = models.BooleanField(default=False)  # Доход/расход
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма"  # Подпись для суммы
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Дата"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    def __str__(self):
        return f"{self.date}: {self.amount} ({'Доход' if self.is_income else 'Расход'})"

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Anomaly(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL)
    # Для хранения обнаруженных аномалий

class FavoriteReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    filters = models.JSONField()  # Хранит настройки фильтрации (например, период, категории)
    # Для сохранения избранных отчётов

class NotificationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    # История отправленных уведомлений

class TelegramLinkToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"


class MonthlyBudget(models.Model):
    """Модель для хранения ежемесячного бюджета"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.CharField(max_length=7)
    planned_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    planned_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"Budget for {self.month}"