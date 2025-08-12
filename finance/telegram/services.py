
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from finance.models import TelegramLinkToken, Transaction, Category, User, MonthlyBudget


def process_start_command(token, telegram_id):
    """Синхронная функция для обработки команды /start"""
    try:
        link_token = TelegramLinkToken.objects.get(token=token)

        # Проверка времени жизни токена (5 минут)
        if link_token.created_at < timezone.now() - timedelta(minutes=5):
            link_token.delete()
            return "❌ Ссылка устарела. Сгенерируйте новую на сайте."

        user = link_token.user
        user.telegram_id = telegram_id
        user.telegram_linked = True
        user.save()
        link_token.delete()

        return (
            "✅ Аккаунт успешно привязан!\n\n"
            "Доступные команды:\n"
            "/today - Отчёт за сегодня\n"
            "/week - Отчёт за неделю\n"
            "/add - Добавить операцию\n"
            "/help - Справка\n\n"
            "Или нажмите на кнопки ниже:"
        )

    except TelegramLinkToken.DoesNotExist:
        return (
            "👋 Привет! Я — ваш финансовый помощник.\n\n"
            "Доступные команды:\n"
            "/today - Отчёт за сегодня\n"
            "/week - Отчёт за неделю\n"
            "/add - Добавить операцию\n"
            "/help - Справка\n\n"
            "Или нажмите на кнопки ниже:"
        )
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def get_today_report(telegram_id):
    """Синхронная функция для получения отчёта за сегодня"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        today = timezone.now().date()

        expenses = Transaction.objects.filter(
            user=user, date=today, category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        income = Transaction.objects.filter(
            user=user, date=today, category__is_income=True
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        return f"📊 Отчёт за сегодня:\nДоходы: {income} ₽\nРасходы: {expenses} ₽"

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан. Перейдите на сайт и привяжите Telegram."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def get_week_report(telegram_id):
    """Синхронная функция для получения отчёта за неделю"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        week_ago = timezone.now().date() - timedelta(days=7)

        expenses = Transaction.objects.filter(
            user=user, date__gte=week_ago, category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        return f"📈 Расходы за неделю: {expenses} ₽"

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def process_add_command(telegram_id, amount, category_name, description):
    """Синхронная функция для добавления операции"""
    try:
        user = User.objects.get(telegram_id=telegram_id)

        # Нормализуем ввод пользователя
        normalized_input = category_name.strip().lower()

        # Получаем все категории пользователя
        user_categories = Category.objects.filter(user=user)

        # Ищем совпадение без учета регистра
        category = None
        for cat in user_categories:
            if cat.name.lower() == normalized_input:
                category = cat
                break

        if not category:
            # Для диагностики: покажем доступные категории
            available_categories = ", ".join([c.name for c in user_categories])
            return (
                f"❌ Категория '{category_name}' не найдена.\n"
                f"Доступные категории: {available_categories}"
            )

        Transaction.objects.create(
            user=user,
            amount=amount,
            category=category,
            description=description
        )

        return f"✅ Операция добавлена: {amount} ₽ ({category.name})"

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def prepare_daily_reports():
    """Синхронная функция для подготовки ежедневных отчётов"""
    reports = []
    try:
        users = User.objects.filter(telegram_linked=True, send_daily_report=True)
        today = timezone.now().date()

        for user in users:
            expenses = Transaction.objects.filter(
                user=user, date=today, category__is_income=False
            ).aggregate(sum=Sum('amount'))['sum'] or 0

            reports.append((
                user.telegram_id,
                f"📅 Ежедневный отчёт:\nСегодня потрачено: {expenses} ₽"
            ))
    except Exception as e:
        print(f"❌ Ошибка при подготовке отчётов: {e}")

    return reports


def create_category(telegram_id, name, is_income):
    """Создает новую категорию"""
    try:
        user = User.objects.get(telegram_id=telegram_id)

        # Проверяем, нет ли уже такой категории
        if Category.objects.filter(user=user, name__iexact=name).exists():
            return f"❌ Категория '{name}' уже существует."

        # Создаем новую категорию
        Category.objects.create(
            user=user,
            name=name,
            is_income=is_income
        )

        return f"✅ Категория '{name}' успешно добавлена!"

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def set_monthly_budget(telegram_id, planned_income, planned_expense):
    """Устанавливает бюджет на текущий месяц"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        current_month = timezone.now().replace(day=1).strftime('%Y-%m')

        # Создаем или обновляем бюджет
        budget, created = MonthlyBudget.objects.update_or_create(
            user=user,
            month=current_month,
            defaults={
                'planned_income': planned_income,
                'planned_expense': planned_expense
            }
        )

        return (
            f"✅ Бюджет на {current_month} установлен:\n"
            f"Доход: {planned_income} ₽\n"
            f"Расход: {planned_expense} ₽"
        )

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def get_budget_recommendations(telegram_id):
    """Генерирует рекомендации на основе бюджета"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        current_month = timezone.now().replace(day=1).strftime('%Y-%m')

        try:
            budget = MonthlyBudget.objects.get(user=user, month=current_month)
        except MonthlyBudget.DoesNotExist:
            return ["📊 Установите бюджет для получения персонализированных рекомендаций."]

        # Аналогичная логика как в home view
        year, month = map(int, current_month.split('-'))
        transactions = Transaction.objects.filter(
            user=user,
            date__year=year,
            date__month=month
        )

        total_income = transactions.filter(category__is_income=True).aggregate(sum=Sum('amount'))['sum'] or 0
        total_expense = transactions.filter(category__is_income=False).aggregate(sum=Sum('amount'))['sum'] or 0

        recommendations = []

        # Анализ доходов
        if budget.planned_income > 0:
            income_diff = total_income - budget.planned_income
            income_percent = (total_income / budget.planned_income * 100) if budget.planned_income else 0

            if income_diff > 0:
                recommendations.append(
                    f"✅ Доходы превысили план на {abs(income_diff):.2f} ₽ ({income_percent:.1f}%)"
                )
            elif income_diff < 0:
                recommendations.append(
                    f"⚠️ Доходы ниже плана на {abs(income_diff):.2f} ₽ ({income_percent:.1f}%)"
                )

        # Анализ расходов
        if budget.planned_expense > 0:
            expense_diff = total_expense - budget.planned_expense
            expense_percent = (total_expense / budget.planned_expense * 100) if budget.planned_expense else 0

            if expense_diff > 0:
                recommendations.append(
                    f"⚠️ Расходы превысили план на {abs(expense_diff):.2f} ₽ ({expense_percent:.1f}%)"
                )
            elif expense_diff < 0:
                recommendations.append(
                    f"✅ Расходы ниже плана на {abs(expense_diff):.2f} ₽ ({expense_percent:.1f}%)"
                )

        # Прогноз на конец месяца
        today = timezone.now().date()
        days_passed = (today - today.replace(day=1)).days + 1
        if days_passed > 0 and budget.planned_expense > 0:
            daily_expense = total_expense / days_passed
            days_in_month = (today.replace(month=today.month % 12 + 1) - timedelta(days=1)).day
            days_remaining = days_in_month - days_passed
            projected_expense = total_expense + (daily_expense * days_remaining)

            if projected_expense > budget.planned_expense:
                over = projected_expense - budget.planned_expense
                recommendations.append(
                    f"⚠️ По текущим тратам вы превысите бюджет на {over:.2f} ₽"
                )
            else:
                remaining = budget.planned_expense - projected_expense
                recommendations.append(
                    f"✅ По текущим тратам вы уложитесь в бюджет, остаток {remaining:.2f} ₽"
                )

        return recommendations

    except User.DoesNotExist:
        return ["❌ Ваш аккаунт не привязан."]
    except Exception as e:
        return [f"❌ Ошибка: {str(e)}"]


def get_detailed_today_report(telegram_id):
    """Подробный отчёт за сегодня"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        today = timezone.now().date()

        # Группировка по категориям
        expenses_by_category = {}
        transactions = Transaction.objects.filter(
            user=user,
            date=today,
            category__is_income=False
        )

        for t in transactions:
            cat_name = t.category.name
            if cat_name not in expenses_by_category:
                expenses_by_category[cat_name] = 0
            expenses_by_category[cat_name] += t.amount

        # Формируем отчёт
        report = f"📊 Подробный отчёт за сегодня ({today}):\n"
        if expenses_by_category:
            for category, amount in expenses_by_category.items():
                report += f"• {category}: {amount} ₽\n"
        else:
            report += "Нет расходов за сегодня.\n"

        return report

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def compare_with_previous_week(telegram_id):
    """Сравнение с прошлой неделей"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        today = timezone.now().date()

        # Текущая неделя
        week_ago = today - timedelta(days=7)
        current_week_expenses = Transaction.objects.filter(
            user=user,
            date__gte=week_ago,
            category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        # Прошлая неделя
        two_weeks_ago = today - timedelta(days=14)
        previous_week_expenses = Transaction.objects.filter(
            user=user,
            date__gte=two_weeks_ago,
            date__lt=week_ago,
            category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        diff = current_week_expenses - previous_week_expenses

        report = f"📈 Сравнение с прошлой неделей:\n"
        report += f"Эта неделя: {current_week_expenses} ₽\n"
        report += f"Прошлая неделя: {previous_week_expenses} ₽\n"

        if diff > 0:
            report += f"Вы потратили на {diff:.2f} ₽ больше. 💸"
        elif diff < 0:
            report += f"Вы сэкономили {abs(diff):.2f} ₽! 🎉"
        else:
            report += "Расходы одинаковы. 🟰"

        return report

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def get_detailed_week_report(telegram_id):
    """Подробный отчёт за неделю"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        week_ago = timezone.now().date() - timedelta(days=7)

        # Группировка по категориям
        expenses_by_category = {}
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=week_ago,
            category__is_income=False
        )

        for t in transactions:
            cat_name = t.category.name
            if cat_name not in expenses_by_category:
                expenses_by_category[cat_name] = 0
            expenses_by_category[cat_name] += t.amount

        # Формируем отчёт
        report = f"📈 Подробный отчёт за неделю:\n"
        if expenses_by_category:
            for category, amount in expenses_by_category.items():
                report += f"• {category}: {amount} ₽\n"
        else:
            report += "Нет расходов за неделю.\n"

        return report

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


def compare_with_previous_month(telegram_id):
    """Сравнение с прошлым месяцем"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        today = timezone.now().date()
        current_month_str = today.replace(day=1).strftime('%Y-%m')

        # Текущий месяц
        current_year, current_month = map(int, current_month_str.split('-'))
        current_month_expenses = Transaction.objects.filter(
            user=user,
            date__year=current_year,
            date__month=current_month,
            category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        # Прошлый месяц
        if current_month == 1:
            previous_year, previous_month = current_year - 1, 12
        else:
            previous_year, previous_month = current_year, current_month - 1

        previous_month_expenses = Transaction.objects.filter(
            user=user,
            date__year=previous_year,
            date__month=previous_month,
            category__is_income=False
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        diff = current_month_expenses - previous_month_expenses

        report = f"📅 Сравнение с прошлым месяцем:\n"
        report += f"Этот месяц: {current_month_expenses} ₽\n"
        report += f"Прошлый месяц: {previous_month_expenses} ₽\n"

        if diff > 0:
            report += f"Вы потратили на {diff:.2f} ₽ больше. 💸"
        elif diff < 0:
            report += f"Вы сэкономили {abs(diff):.2f} ₽! 🎉"
        else:
            report += "Расходы одинаковы. 🟰"

        return report

    except User.DoesNotExist:
        return "❌ Ваш аккаунт не привязан."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"