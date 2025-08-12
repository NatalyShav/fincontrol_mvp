import uuid
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
from django.contrib import messages
from .forms import TransactionForm, RegisterForm, CategoryForm
from .models import Category,Transaction, Anomaly, FavoriteReport
from pathlib import Path
from .models import TelegramLinkToken
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import json
from .models import MonthlyBudget
from .forms import MonthlyBudgetForm
from django.utils import timezone



def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'finance/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('add_operation')
        else:
            return render(request, 'finance/login.html', {'error': 'Неверные данные'})
    return render(request, 'finance/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_operation(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)  # ← Передаём пользователя!
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('history')
    else:
        form = TransactionForm(user=request.user)  # ← Здесь тоже!
    return render(request, 'finance/add_operation.html', {'form': form})

@login_required
def history_view(request):
    transactions = Transaction.objects.filter(user=request.user)

    # Фильтр по периоду
    period = request.GET.get('period')
    if period == 'today':
        transactions = transactions.filter(date=timezone.now().date())
    elif period == 'week':
        start_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
        transactions = transactions.filter(date__gte=start_week)
    elif period == 'month':
        transactions = transactions.filter(date__month=timezone.now().month,
                                           date__year=timezone.now().year)

    return render(request, 'finance/history.html', {
        'transactions': transactions.order_by('-date'),
        'period': period
    })


@login_required
def analytics_view(request):
    # Здесь будет логика для получения данных
    recommendations = Recommendation.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'finance/analytics.html', {'recommendations': recommendations})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'finance/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'finance/category_form.html', {'form': form, 'title': 'Добавить категорию'})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'finance/category_form.html', {'form': form, 'title': 'Редактировать категорию'})

@login_required
def home(request):
    # Получаем все операции текущего пользователя
    transactions = Transaction.objects.filter(user=request.user)

    # Считаем доходы и расходы
    total_income = transactions.filter(category__is_income=True).aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = transactions.filter(category__is_income=False).aggregate(sum=Sum('amount'))['sum'] or 0
    balance = total_income - total_expense

    # Последние 3 операции
    recent_transactions = transactions.select_related('category')[:3]

    # Рекомендации (пример простых советов)
    recommendations = []
    if total_expense > 30000:
        recommendations.append("Вы тратите много. Рассмотрите возможность сокращения расходов.")
    if total_income > 0 and total_expense / total_income > 0.7:
        recommendations.append("Ваши расходы составляют более 70% от дохода — обратите внимание на бюджет.")
    if not recommendations:
        recommendations.append("Отличная работа! Вы хорошо управляете своими финансами.")



    chart1 = create_income_expense_chart(request.user)
    chart2 = create_category_pie_chart(request.user)

    print("Chart 1 path:", chart1)
    print("Chart 2 path:", chart2)

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'recommendations': recommendations,
    }
    return render(request, 'finance/index.html', context)


def create_income_expense_chart(user):
    transactions = Transaction.objects.filter(user=user)
    if not transactions.exists():
        return None

    data = []
    for t in transactions:
        data.append({
            'date': t.date,
            'amount': float(t.amount),
            'is_income': t.category.is_income
        })

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.strftime('%Y-%m')

    income = df[df['is_income']].groupby('year_month')['amount'].sum()
    expense = df[~df['is_income']].groupby('year_month')['amount'].sum()

    plt.figure(figsize=(10, 5))
    if not income.empty:
        plt.plot(income.index, income.values, label='Доходы', color='green', marker='o')
    if not expense.empty:
        plt.plot(expense.index, expense.values, label='Расходы', color='red', marker='s')

    plt.title('Доходы и расходы по месяцам')
    plt.xlabel('Месяц')
    plt.ylabel('Сумма (₽)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Путь к файлу
    static_dir = settings.STATICFILES_DIRS[0]  # Это Path
    chart_path = Path(static_dir) / 'images' / 'income_expense.png'
    chart_path.parent.mkdir(parents=True, exist_ok=True)  # Создаёт папку, если её нет

    try:
        plt.savefig(chart_path, dpi=100)
        plt.close()
        print(f"✅ График сохранён: {chart_path}")
        return '/static/images/income_expense.png'
    except Exception as e:
        print(f"❌ Ошибка сохранения графика: {e}")
        plt.close()
        return None


def create_category_pie_chart(user):
    expenses = Transaction.objects.filter(user=user, category__is_income=False)
    if not expenses.exists():
        return None

    data = []
    for t in expenses:
        data.append({
            'category': t.category.name,
            'amount': float(t.amount)
        })

    df = pd.DataFrame(data)
    category_totals = df.groupby('category')['amount'].sum()

    plt.figure(figsize=(8, 8))
    colors = plt.cm.Set3(range(len(category_totals)))
    plt.pie(category_totals.values, labels=category_totals.index, autopct='%1.1f%%', startangle=90, colors=colors)
    plt.title('Распределение расходов по категориям')
    plt.tight_layout()

    static_dir = settings.STATICFILES_DIRS[0]
    chart_path = Path(static_dir) / 'images' / 'category_pie.png'
    chart_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        plt.savefig(chart_path, dpi=100)
        plt.close()
        print(f"✅ Диаграмма сохранена: {chart_path}")
        return '/static/images/category_pie.png'
    except Exception as e:
        print(f"❌ Ошибка сохранения диаграммы: {e}")
        plt.close()
        return None


@login_required
def generate_telegram_link(request):
    # Удаляем старый токен, если есть
    TelegramLinkToken.objects.filter(user=request.user).delete()

    # Генерируем уникальный токен
    token = str(uuid.uuid4())
    TelegramLinkToken.objects.create(user=request.user, token=token)

    # Ссылка для открытия бота с токеном
    link = f"https://t.me/fincontrol_test_Bot?start={token}"

    return render(request, 'finance/telegram_link.html', {'link': link})


@csrf_exempt
@login_required
def api_create_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            is_income = data.get('is_income', False)

            if not name:
                return JsonResponse({'error': 'Название категории обязательно'}, status=400)

            # Проверяем, нет ли уже такой категории у пользователя
            if Category.objects.filter(user=request.user, name__iexact=name).exists():
                return JsonResponse({'error': 'Категория с таким названием уже существует'}, status=400)

            # Создаем новую категорию
            category = Category.objects.create(
                user=request.user,
                name=name,
                is_income=is_income
            )

            return JsonResponse({
                'id': category.id,
                'name': category.name
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


@login_required
def budget_view(request):
    # Текущий месяц в формате "YYYY-MM"
    current_month = timezone.now().strftime('%Y-%m')
    print("📅 Текущий месяц:", current_month)

    # Получаем или создаём бюджет
    budget, created = MonthlyBudget.objects.get_or_create(
        user=request.user,
        month=current_month,
        defaults={'planned_income': 0, 'planned_expense': 0}
    )
    print("🔍 Бюджет:", budget.id, "Создан:", created)

    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            print("✅ Сохранено:", budget.planned_income, budget.planned_expense)
            messages.success(request, "Бюджет успешно сохранен!")
            return redirect('budget')
        else:
            print("❌ Ошибки формы:", form.errors)
    else:
        form = MonthlyBudgetForm(instance=budget)

    # Получаем транзакции за текущий месяц
    # Преобразуем строку "2025-08" в объект даты для фильтрации
    year, month = map(int, current_month.split('-'))

    transactions = Transaction.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )

    # Считаем фактические доходы и расходы
    total_income = transactions.filter(category__is_income=True).aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = transactions.filter(category__is_income=False).aggregate(sum=Sum('amount'))['sum'] or 0

    # Разница
    income_diff = total_income - budget.planned_income
    expense_diff = total_expense - budget.planned_expense

    # История бюджета
    budget_history = MonthlyBudget.objects.filter(
        user=request.user,
        month__lte=current_month
    ).order_by('-month')[:3]

    context = {
        'form': form,
        'budget': budget,
        'total_income': total_income,
        'total_expense': total_expense,
        'income_diff': income_diff,
        'expense_diff': expense_diff,
        'income_diff_abs': abs(income_diff),
        'expense_diff_abs': abs(expense_diff),
        'budget_history': budget_history
    }
    return render(request, 'finance/budget.html', context)

@login_required
def home(request):
    """Главная страница с аналитикой"""
    transactions = Transaction.objects.filter(user=request.user)

    # Получаем бюджет на текущий месяц
    current_month = timezone.now().replace(day=1)
    try:
        budget = MonthlyBudget.objects.get(user=request.user, month=current_month)
    except MonthlyBudget.DoesNotExist:
        budget = None

    # Считаем фактические доходы и расходы
    total_income = transactions.filter(category__is_income=True).aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = transactions.filter(category__is_income=False).aggregate(sum=Sum('amount'))['sum'] or 0
    balance = total_income - total_expense

    # Генерируем рекомендации
    recommendations = []

    # 1. Стандартные рекомендации
    if total_expense > 30000:
        recommendations.append("Вы тратите много. Рассмотрите возможность сокращения расходов.")
    if total_income > 0 and total_expense / total_income > 0.7:
        recommendations.append("Ваши расходы составляют более 70% от дохода — обратите внимание на бюджет.")

    # 2. Рекомендации на основе бюджета
    if budget:
        # Анализ доходов
        if budget.planned_income > 0:
            income_diff = total_income - budget.planned_income
            income_percent = (total_income / budget.planned_income * 100) if budget.planned_income else 0

            if income_diff > 0:
                recommendations.append(
                    f"✅ Ваши доходы превысили план на {abs(income_diff):.2f} ₽ "
                    f"({income_percent:.1f}% от запланированного). Отлично!"
                )
            elif income_diff < 0:
                recommendations.append(
                    f"⚠️ Ваши доходы ниже плана на {abs(income_diff):.2f} ₽ "
                    f"({income_percent:.1f}% от запланированного). "
                    "Рассмотрите возможности увеличения доходов."
                )

        # Анализ расходов
        if budget.planned_expense > 0:
            expense_diff = total_expense - budget.planned_expense
            expense_percent = (total_expense / budget.planned_expense * 100) if budget.planned_expense else 0

            if expense_diff > 0:
                recommendations.append(
                    f"⚠️ Ваши расходы превысили план на {abs(expense_diff):.2f} ₽ "
                    f"({expense_percent:.1f}% от запланированного). "
                    "Обратите внимание на категории с наибольшими отклонениями."
                )
            elif expense_diff < 0:
                recommendations.append(
                    f"✅ Ваши расходы ниже плана на {abs(expense_diff):.2f} ₽ "
                    f"({expense_percent:.1f}% от запланированного). "
                    "Отлично! Вы укладываетесь в бюджет."
                )

        # Прогноз на конец месяца
        days_passed = (timezone.now().date() - current_month.date()).days + 1
        if days_passed > 0 and budget.planned_expense > 0:
            daily_expense = total_expense / days_passed
            days_remaining = (current_month.replace(month=current_month.month % 12 + 1) - timedelta(
                days=1)).day - days_passed
            projected_expense = total_expense + (daily_expense * days_remaining)

            if projected_expense > budget.planned_expense:
                over = projected_expense - budget.planned_expense
                recommendations.append(
                    f"⚠️ По текущим тратам вы превысите бюджет на конец месяца на {over:.2f} ₽"
                )
            else:
                remaining = budget.planned_expense - projected_expense
                recommendations.append(
                    f"✅ По текущим тратам вы уложитесь в бюджет, остаток составит {remaining:.2f} ₽"
                )

    # 3. Анализ по категориям
    if transactions.filter(category__is_income=False).exists():
        # Получаем топ-3 категории с наибольшими расходами
        category_expenses = {}
        for transaction in transactions.filter(category__is_income=False):
            category_name = transaction.category.name
            if category_name not in category_expenses:
                category_expenses[category_name] = 0
            category_expenses[category_name] += transaction.amount

        # Сортируем и получаем топ-3
        top_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)[:3]

        for category, amount in top_categories:
            if amount > 5000:  # Порог для "больших" расходов
                recommendations.append(
                    f"💡 Вы тратите много на '{category}' — {amount:.2f} ₽. "
                    "Может быть, есть возможности для оптимизации?"
                )

    # 4. Если нет рекомендаций
    if not recommendations:
        recommendations.append("Отличная работа! Вы хорошо управляете своими финансами.")

    # Остальная логика
    recent_transactions = transactions.select_related('category')[:3]
    chart1 = create_income_expense_chart(request.user)
    chart2 = create_category_pie_chart(request.user)
    chart3 = create_budget_chart(request.user)

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'recommendations': recommendations,
        'chart_income_expense': chart1,
        'chart_category_distribution': chart2,
        'budget': budget,
        'chart_budget_comparison': chart3
    }
    return render(request, 'finance/index.html', context)


def create_budget_chart(user):
    """Создает график сравнения плана и факта"""
    current_month = datetime.now().replace(day=1)
    next_month = current_month + timedelta(days=31)
    next_month = next_month.replace(day=1)

    # Получаем транзакции за текущий месяц
    transactions = Transaction.objects.filter(
        user=user,
        date__gte=current_month,
        date__lt=next_month
    )

    # Считаем фактические доходы и расходы
    total_income = transactions.filter(category__is_income=True).aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = transactions.filter(category__is_income=False).aggregate(sum=Sum('amount'))['sum'] or 0

    # Получаем бюджет
    try:
        budget = MonthlyBudget.objects.get(user=user, month=current_month)
        planned_income = float(budget.planned_income)
        planned_expense = float(budget.planned_expense)
    except MonthlyBudget.DoesNotExist:
        return None

    # Строим график
    plt.figure(figsize=(10, 6))

    # План
    plt.bar(['План', 'Факт'], [planned_income, total_income], color=['skyblue', 'green'], alpha=0.7, label='Доходы')
    plt.bar(['План', 'Факт'], [planned_expense, total_expense], bottom=[planned_income, total_income],
            color=['salmon', 'red'], alpha=0.7, label='Расходы')

    plt.title(f'Сравнение плана и факта за {current_month.strftime("%B %Y")}')
    plt.ylabel('Сумма (₽)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Сохраняем график
    static_dir = settings.STATICFILES_DIRS[0]
    chart_path = Path(static_dir) / 'images' / 'budget_comparison.png'
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(chart_path)
    plt.close()

    return '/static/images/budget_comparison.png'