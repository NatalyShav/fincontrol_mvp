from aiogram import Router, types
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from finance.telegram.keyboards import get_main_menu, get_remove_keyboard
from finance.telegram.services import (
    process_start_command,
    get_today_report,
    get_week_report,
    process_add_command,
    prepare_daily_reports,
    create_category,
    get_detailed_today_report,
    compare_with_previous_week,
    get_detailed_week_report,
    compare_with_previous_month,
    set_monthly_budget,
    get_budget_recommendations,
    User  # Добавлен импорт User
)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split(" ")

    # Проверяем, есть ли у пользователя telegram_id
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.from_user.id)

        # Если пользователь уже привязан
        if user.telegram_linked:
            # Показываем главное меню
            await message.answer(
                f"👋 С возвращением, {user.username}!\n\n"
                "Чем могу помочь?",
                reply_markup=get_main_menu()
            )
            return
    except User.DoesNotExist:
        pass  # Пользователь ещё не привязан

    # Обработка токена привязки
    if len(args) > 1:
        token = args[1]
        try:
            result = await sync_to_async(process_start_command)(token, message.from_user.id)
            await message.answer(result, reply_markup=get_main_menu())
            return
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())
            return

    # Если это простой /start без токена
    result = await sync_to_async(process_start_command)(None, message.from_user.id)
    await message.answer(result, reply_markup=get_main_menu())


@router.message(Command("today"))
async def cmd_today(message: types.Message):
    result = await sync_to_async(get_today_report)(message.from_user.id)

    # Создаём инлайн-кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Подробнее", callback_data="report_detailed")],
        [InlineKeyboardButton(text="🔄 Сравнить с прошлой неделей", callback_data="report_compare_week")],
        [InlineKeyboardButton(text="➕ Добавить трату", callback_data="add_expense")]
    ])

    await message.answer(result, reply_markup=keyboard)


@router.message(Command("week"))
async def cmd_week(message: types.Message):
    result = await sync_to_async(get_week_report)(message.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Подробнее", callback_data="report_detailed")],
        [InlineKeyboardButton(text="🔄 Сравнить с прошлой неделей", callback_data="report_compare_week")],
        [InlineKeyboardButton(text="➕ Добавить трату", callback_data="add_expense")]
    ])

    await message.answer(result, reply_markup=keyboard)


@router.message(Command("add"))
async def cmd_add(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.answer(
            "Чтобы добавить операцию, используйте команду:\n"
            "/add сумма категория [описание]\n\n"
            "Пример:\n"
            "/add 500 Еда обед",
            reply_markup=get_main_menu()
        )
        return

    try:
        amount = float(parts[1])
        category_name = parts[2].split(" ")[0]
        description = " ".join(parts[2].split(" ")[1:]) if len(parts[2].split(" ")) > 1 else ""

        # Выполняем всю логику в синхронной функции
        result = await sync_to_async(process_add_command)(
            message.from_user.id, amount, category_name, description
        )
        await message.answer(result, reply_markup=get_main_menu())
    except ValueError:
        await message.answer("❌ Сумма должна быть числом.", reply_markup=get_main_menu())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Отображает главное меню с кнопками"""
    await message.answer(
        "Меню главных команд:",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📚 Справка по использованию бота:\n\n"
        "📌 /today - Отчёт о расходах за сегодня\n"
        "📌 /week - Отчёт о расходах за неделю\n"
        "📌 /add сумма категория [описание] - Добавить операцию\n"
        "    Пример: /add 500 Еда обед\n"
        "📌 /menu - Показать главное меню\n\n"
        "💡 Совет: Вы можете использовать кнопки ниже для быстрого доступа к командам."
    )
    await message.answer(help_text, reply_markup=get_main_menu())


# Обработка нажатия на кнопки
@router.message(lambda message: message.text == "/today")
async def button_today(message: types.Message):
    result = await sync_to_async(get_today_report)(message.from_user.id)
    await message.answer(result, reply_markup=get_main_menu())


@router.message(lambda message: message.text == "/week")
async def button_week(message: types.Message):
    result = await sync_to_async(get_week_report)(message.from_user.id)
    await message.answer(result, reply_markup=get_main_menu())


@router.message(lambda message: message.text == "/add")
async def button_add(message: types.Message):
    await message.answer(
        "Чтобы добавить операцию, используйте команду:\n"
        "/add сумма категория [описание]\n\n"
        "Пример:\n"
        "/add 500 Еда обед",
        reply_markup=get_main_menu()
    )


@router.message(lambda message: message.text == "/help")
async def button_help(message: types.Message):
    help_text = (
        "📚 Справка по использованию бота:\n\n"
        "📌 /today - Отчёт о расходах за сегодня\n"
        "📌 /week - Отчёт о расходах за неделю\n"
        "📌 /add сумма категория [описание] - Добавить операцию\n"
        "    Пример: /add 500 Еда обед\n"
        "📌 /menu - Показать главное меню\n\n"
        "💡 Совет: Вы можете использовать кнопки ниже для быстрого доступа к командам."
    )
    await message.answer(help_text, reply_markup=get_main_menu())


@router.message(lambda message: message.text == "Скрыть меню")
async def hide_menu(message: types.Message):
    await message.answer(
        "Меню скрыто. Чтобы снова его открыть, отправьте /menu",
        reply_markup=get_remove_keyboard()
    )


@router.message(Command("newcategory"))
async def cmd_newcategory(message: types.Message):
    help_text = (
        "📝 Чтобы создать новую категорию, используйте:\n"
        "/createcategory название тип\n\n"
        "Тип может быть:\n"
        "income - для доходов\n"
        "expense - для расходов\n\n"
        "Пример:\n"
        "/createcategory Транспорт expense"
    )
    await message.answer(help_text, reply_markup=get_main_menu())


@router.message(Command("createcategory"))
async def cmd_createcategory(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.answer(
            "❌ Используйте: /createcategory название тип\n"
            "Тип: income или expense",
            reply_markup=get_main_menu()
        )
        return

    try:
        name = parts[1]
        type_str = parts[2].lower()

        if type_str not in ['income', 'expense']:
            await message.answer(
                "❌ Неверный тип. Используйте: income или expense",
                reply_markup=get_main_menu()
            )
            return

        is_income = (type_str == 'income')

        # Создаем категорию
        result = await sync_to_async(create_category)(
            message.from_user.id, name, is_income
        )

        await message.answer(result, reply_markup=get_main_menu())

    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


@router.message(Command("setbudget"))
async def cmd_setbudget(message: types.Message):
    """Показывает инструкцию по установке бюджета"""
    help_text = (
        "📝 Чтобы установить бюджет, используйте:\n"
        "/budget [доход] [расход]\n\n"
        "Пример:\n"
        "/budget 50000 35000"
    )
    await message.answer(help_text, reply_markup=get_main_menu())


@router.message(Command("budget"))
async def cmd_setbudget_values(message: types.Message):
    """Устанавливает значения бюджета"""
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(
            "❌ Используйте: /budget [доход] [расход]\n"
            "Пример: /budget 50000 35000",
            reply_markup=get_main_menu()
        )
        return

    try:
        planned_income = float(parts[1])
        planned_expense = float(parts[2])

        # Сохраняем бюджет
        result = await sync_to_async(set_monthly_budget)(
            message.from_user.id, planned_income, planned_expense
        )

        # Получаем рекомендации
        recommendations = await sync_to_async(get_budget_recommendations)(message.from_user.id)

        response = f"{result}\n\n📊 Анализ бюджета:\n"
        response += "\n".join(recommendations)

        await message.answer(response, reply_markup=get_main_menu())
    except ValueError:
        await message.answer(
            "❌ Доход и расход должны быть числами",
            reply_markup=get_main_menu()
        )


# Обработчики callback-запросов
@router.callback_query(lambda c: c.data == "report_detailed")
async def callback_detailed_report(callback: CallbackQuery):
    result = await sync_to_async(get_detailed_today_report)(callback.from_user.id)
    await callback.message.edit_text(result)
    await callback.answer()


@router.callback_query(lambda c: c.data == "report_compare_week")
async def callback_compare_week(callback: CallbackQuery):
    result = await sync_to_async(compare_with_previous_week)(callback.from_user.id)
    await callback.message.edit_text(result)
    await callback.answer()


@router.callback_query(lambda c: c.data == "add_expense")
async def callback_add_expense(callback: CallbackQuery):
    await callback.message.answer(
        "Чтобы добавить операцию, используйте:\n"
        "/add сумма категория [описание]\n\n"
        "Пример:\n"
        "/add 500 Еда обед"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "report_detailed_week")
async def callback_detailed_week_report(callback: CallbackQuery):
    result = await sync_to_async(get_detailed_week_report)(callback.from_user.id)
    await callback.message.edit_text(result)
    await callback.answer()


@router.callback_query(lambda c: c.data == "report_compare_month")
async def callback_compare_month(callback: CallbackQuery):
    result = await sync_to_async(compare_with_previous_month)(callback.from_user.id)
    await callback.message.edit_text(result)
    await callback.answer()