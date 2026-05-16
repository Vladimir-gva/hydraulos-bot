#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydraulos Calculator Bot v2.0
Proekt: «Gidravlika i kalibrovochnaya model nastrojki organnyh trub»
Avtor: Galuzij Nikolaj Vladimirovich, 6 klass, 2026

Formula:
L = (82875 + 150*T) * (1 + p/98000) / f  -  0.3*d
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ──────────────────────────────────────────────
# ВСТАВЬТЕ СЮДА ТОКЕН ОТ @BotFather
# ──────────────────────────────────────────────
BOT_TOKEN = "8758504537:AAHeKBS-yrwKG5BoPwNKzmhQq7-XlgI-Sx0"
# ──────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Состояния диалога
SELECT_NOTE, ENTER_DIAMETER, ENTER_TEMP, ENTER_PRESSURE = range(4)

# Ноты с частотами
NOTES = {
    "До₁  (C₁)":   32.70,
    "Ре₁  (D₁)":   36.71,
    "Ми₁  (E₁)":   41.20,
    "Фа₁  (F₁)":   43.65,
    "Соль₁(G₁)":   49.00,
    "Ля₁  (A₁)":   55.00,
    "Си₁  (B₁)":   61.74,
    "До₂  (C₂)":   65.41,
    "Ре₂  (D₂)":   73.42,
    "Ми₂  (E₂)":   82.41,
    "Фа₂  (F₂)":   87.31,
    "Соль₂(G₂)":   98.00,
    "Ля₂  (A₂)":  110.00,
    "Си₂  (B₂)":  123.47,
    "До₃  (C₃)":  130.81,
    "Ре₃  (D₃)":  146.83,
    "Ми₃  (E₃)":  164.81,
    "Фа₃  (F₃)":  174.61,
    "Соль₃(G₃)":  196.00,
    "Ля₃  (A₃)":  220.00,
    "Си₃  (B₃)":  246.94,
    "До₄  (C₄)":  261.63,
    "Ре₄  (D₄)":  293.66,
    "Ми₄  (E₄)":  329.63,
    "Фа₄  (F₄)":  349.23,
    "Соль₄(G₄)":  392.00,
    "Ля₄  (A₄)":  440.00,
    "Си₄  (B₄)":  493.88,
    "До₅  (C₅)":  523.25,
    "Ре₅  (D₅)":  587.33,
    "Ми₅  (E₅)":  659.26,
    "Фа₅  (F₅)":  698.46,
    "Соль₅(G₅)":  783.99,
    "Ля₅  (A₅)":  880.00,
}

# Допустимые диапазоны
D_MIN, D_MAX = 5.0,   100.0
T_MIN, T_MAX = -20.0,  50.0
P_MIN, P_MAX = 0.0,  50000.0
L_MIN, L_MAX = 10.0, 3000.0


def calc_length(f, d, t, p):
    return (82875.0 + 150.0 * t) * (1.0 + p / 98000.0) / f - 0.3 * d


def format_result(note, f, d, t, p):
    L = calc_length(f, d, t, p)
    speed = 82875.0 + 150.0 * t
    pc    = 1.0 + p / 98000.0
    ec    = 0.3 * d

    warn = ""
    if   L < L_MIN: warn = "\nПредупреждение: труба очень короткая - проверьте параметры."
    elif L > L_MAX: warn = "\nПредупреждение: труба очень длинная - проверьте параметры."

    return (
        "*Результат расчёта*\n"
        "----------------------------\n"
        f"Нота:         *{note.strip()}*\n"
        f"Частота:      *{f:.2f} Гц*\n"
        f"Диаметр:      *{d:.1f} мм*\n"
        f"Температура:  *{t:.1f} °C*\n"
        f"Давление:     *{p:.0f} Па*\n"
        "----------------------------\n"
        f"*Длина трубы: {L:.1f} мм*\n"
        "----------------------------\n"
        "*Детали расчёта:*\n"
        f"  82875 + 150x{t} = {speed:.0f} мм·Гц\n"
        f"  Поправка давления: x{pc:.5f}\n"
        f"  Поправка конца:   -{ec:.2f} мм\n"
        f"  L = {speed:.0f}x{pc:.5f}/{f:.2f} - {ec:.2f}\n"
        f"  Точность: +-2-3 мм{warn}"
    )


HELP_TEXT = (
    "*СПРАВКА - Методика расчёта*\n"
    "----------------------------\n\n"
    "*Физическая основа*\n"
    "Звук в органной трубе - это стоячая волна.\n"
    "Длина закрытой трубы = 1/4 длины волны.\n"
    "Чем длиннее труба - тем ниже нота.\n\n"
    "*Формула калибровочной модели:*\n"
    "`L = (82875 + 150*T) * (1 + p/98000) / f - 0.3*d`\n\n"
    "*Параметры:*\n"
    "L - длина трубы (мм)\n"
    "T - температура воздуха (°C)\n"
    "f - частота ноты (Гц)\n"
    "p - избыточное давление воды (Па)\n"
    "d - внутренний диаметр трубы (мм)\n\n"
    "*Точность модели:* +-2-3 мм\n"
    "_(подтверждено экспериментально)_\n\n"
    "----------------------------\n"
    "_Проект: «Гидравлика и калибровочная_\n"
    "_модель настройки органных труб»_\n"
    "_Галузий Николай Владимирович, 6 кл., 2026_"
)


def note_keyboard_p1():
    note_list = list(NOTES.keys())
    keyboard, row = [], []
    for name in note_list[:14]:
        row.append(InlineKeyboardButton(
            name.split("(")[0].strip(), callback_data=f"note:{name}"
        ))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton(">> Октавы 3-5", callback_data="page:2")])
    return InlineKeyboardMarkup(keyboard)


def note_keyboard_p2():
    note_list = list(NOTES.keys())
    keyboard, row = [], []
    for name in note_list[14:]:
        row.append(InlineKeyboardButton(
            name.split("(")[0].strip(), callback_data=f"note:{name}"
        ))
        if len(row) == 2:
            keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("<< Октавы 1-2", callback_data="page:1")])
    return InlineKeyboardMarkup(keyboard)


def result_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Новый расчёт", callback_data="cmd:start")],
        [InlineKeyboardButton("Справка",      callback_data="cmd:help")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Новый расчёт", callback_data="cmd:start")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    text = (
        "*Hydraulos Calculator v2.0*\n"
        "Калибровочная модель органных труб\n\n"
        "`L = (82875+150*T)*(1+p/98000)/f - 0.3*d`\n\n"
        "Выберите *ноту* (октавы 1-2):"
    )
    if update.message:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=note_keyboard_p1()
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=note_keyboard_p1()
        )
    return SELECT_NOTE


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            HELP_TEXT, parse_mode="Markdown", reply_markup=back_keyboard()
        )
    else:
        await update.message.reply_text(
            HELP_TEXT, parse_mode="Markdown", reply_markup=back_keyboard()
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "page:1":
        await query.edit_message_text(
            "Выберите ноту (октавы 1-2):", reply_markup=note_keyboard_p1()
        )
        return SELECT_NOTE

    if data == "page:2":
        await query.edit_message_text(
            "Выберите ноту (октавы 3-5):", reply_markup=note_keyboard_p2()
        )
        return SELECT_NOTE

    if data.startswith("note:"):
        note_name = data[5:]
        freq = NOTES.get(note_name)
        if not freq:
            await query.edit_message_text("Нота не найдена. /start")
            return ConversationHandler.END
        context.user_data["note"] = note_name
        context.user_data["freq"] = freq
        await query.edit_message_text(
            f"Нота: *{note_name.strip()}* ({freq} Гц)\n\n"
            f"Введите *внутренний диаметр трубы* (мм):\n"
            f"_Допустимо: {D_MIN}-{D_MAX} мм. Например: 20_",
            parse_mode="Markdown",
        )
        return ENTER_DIAMETER

    if data == "cmd:start":
        return await start(update, context)

    if data == "cmd:help":
        await help_handler(update, context)
        return ConversationHandler.END

    return SELECT_NOTE


async def enter_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(",", ".")
    try:
        d = float(text)
    except ValueError:
        await update.message.reply_text(
            "Введите число. Например: `20`", parse_mode="Markdown"
        )
        return ENTER_DIAMETER
    if not (D_MIN <= d <= D_MAX):
        await update.message.reply_text(
            f"Диаметр от {D_MIN} до {D_MAX} мм. Попробуйте ещё раз:"
        )
        return ENTER_DIAMETER
    context.user_data["diameter"] = d
    await update.message.reply_text(
        f"Диаметр: *{d} мм*\n\n"
        f"Введите *температуру воздуха* (°C):\n"
        f"_Допустимо: от {T_MIN} до {T_MAX} °C. Например: 20_",
        parse_mode="Markdown",
    )
    return ENTER_TEMP


async def enter_temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(",", ".")
    try:
        t = float(text)
    except ValueError:
        await update.message.reply_text(
            "Введите число. Например: `20` или `-5`", parse_mode="Markdown"
        )
        return ENTER_TEMP
    if not (T_MIN <= t <= T_MAX):
        await update.message.reply_text(
            f"Температура от {T_MIN} до {T_MAX} °C. Попробуйте ещё раз:"
        )
        return ENTER_TEMP
    context.user_data["temp"] = t
    await update.message.reply_text(
        f"Температура: *{t} °C*\n\n"
        f"Введите *избыточное давление воды* (Па):\n"
        f"_Допустимо: {P_MIN}-{P_MAX} Па.\n"
        f"Например: 1000 Па = примерно 10 см водяного столба\n"
        f"0 - без давления воды_",
        parse_mode="Markdown",
    )
    return ENTER_PRESSURE


async def enter_pressure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().replace(",", ".")
    try:
        p = float(text)
    except ValueError:
        await update.message.reply_text(
            "Введите число. Например: `1000` или `0`", parse_mode="Markdown"
        )
        return ENTER_PRESSURE
    if not (P_MIN <= p <= P_MAX):
        await update.message.reply_text(
            f"Давление от {P_MIN} до {P_MAX} Па. Попробуйте ещё раз:"
        )
        return ENTER_PRESSURE

    note = context.user_data["note"]
    freq = context.user_data["freq"]
    d    = context.user_data["diameter"]
    t    = context.user_data["temp"]

    result = format_result(note, freq, d, t, p)
    await update.message.reply_text(
        result, parse_mode="Markdown", reply_markup=result_keyboard()
    )
    logger.info(
        f"Raschet: {note}, f={freq}, d={d}, T={t}, p={p}, "
        f"L={calc_length(freq,d,t,p):.1f}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено. /start - начать заново.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Нажмите /start чтобы начать расчёт")


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ОШИБКА: Вставьте токен бота в переменную BOT_TOKEN")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_handler, pattern="^cmd:start$"),
        ],
        states={
            SELECT_NOTE:    [CallbackQueryHandler(button_handler)],
            ENTER_DIAMETER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_diameter),
                CallbackQueryHandler(button_handler),
            ],
            ENTER_TEMP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_temp),
                CallbackQueryHandler(button_handler),
            ],
            ENTER_PRESSURE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_pressure),
                CallbackQueryHandler(button_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(help_handler, pattern="^cmd:help$"))
    app.add_handler(CallbackQueryHandler(start,        pattern="^cmd:start$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    print("Hydraulos Calculator Bot v2.0 zapushchen!")
    print("Nazhmite Ctrl+C dlya ostanovki.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
