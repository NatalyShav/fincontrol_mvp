from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Category, Transaction, Recommendation, Anomaly, FavoriteReport, MonthlyBudget


User = get_user_model()

# finance/forms.py
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'is_income', 'parent']
        labels = {
            'name': 'Название',
            'is_income': 'Тип операции',
            'parent': 'Родительская категория (опционально)',
        }
        widgets = {
            'is_income': forms.RadioSelect(choices=((False, 'Расход'), (True, 'Доход')))
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'date', 'category', 'description']
        labels = {
            'amount': 'Сумма',
            'date': 'Дата',
            'category': 'Категория',
            'description': 'Описание',
        }

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        # Опционально: можно добавить подсказки (help_texts)
        help_texts = {
            'amount': 'Введите сумму (например, 1500.50)',
            'description': 'Можно оставить пустым',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Извлекаем пользователя из параметров
        super().__init__(*args, **kwargs)
        if user:
            # Ограничиваем выбор категорий — только те, что принадлежат пользователю
            self.fields['category'].queryset = Category.objects.filter(user=user)

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        fields = ['text']

class AnomalyForm(forms.ModelForm):
    class Meta:
        model = Anomaly
        fields = ['description', 'transaction']

class FavoriteReportForm(forms.ModelForm):
    class Meta:
        model = FavoriteReport
        fields = ['name', 'filters']

class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]


class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ['month', 'planned_income', 'planned_expense']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month'}),
        }
        labels = {
            'month': 'Месяц',
            'planned_income': 'Запланированный доход',
            'planned_expense': 'Запланированные расходы',
        }

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        planned_income = cleaned_data.get('planned_income')
        planned_expense = cleaned_data.get('planned_expense')

        if planned_income is not None and planned_income < 0:
            self.add_error('planned_income', 'Доход не может быть отрицательным')

        if planned_expense is not None and planned_expense < 0:
            self.add_error('planned_expense', 'Расходы не могут быть отрицательными')

        return cleaned_data