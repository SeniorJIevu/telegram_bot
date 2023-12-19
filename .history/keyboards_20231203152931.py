from aiogram.types import (InlineKeyboardMarkup,
                           InlineKeyboardButton)

from constants import *

# send_start
keyboard_send_start = InlineKeyboardMarkup(resize_keyboard=True)
keyboard_send_start.add(InlineKeyboardButton(text="Продолжить 👉🏻", callback_data='Продолжить 👉🏻'))

# select gender
keyboard_select_gender = InlineKeyboardMarkup(resize_keyboard=True)
button_1 = InlineKeyboardButton(text="🚺 Женский", callback_data="🚺 Женский")
button_2 = InlineKeyboardButton(text="🚹 Мужской", callback_data="🚹 Мужской")
keyboard_select_gender.add(*[button_1, button_2])



# select tarif keyboards without free
keyboard_select_tarif2 = InlineKeyboardMarkup(resize_keyboard=True, row_width=1)
button_2 = InlineKeyboardButton(text=SEND_TARIF_PREMIUM, callback_data=SEND_TARIF_PREMIUM)
button_3 = InlineKeyboardButton(text=SETTINGS, callback_data=SETTINGS)
keyboard_select_tarif2.add(*[button_1, button_2])

# select other tarif keyboards
keyboard_select_other_tarif = InlineKeyboardMarkup(
    resize_keyboard=True, row_width=1
)
button_1 = InlineKeyboardButton(text=SEND_SELECT_OTHER_TARIF, callback_data=SEND_SELECT_OTHER_TARIF)
keyboard_select_other_tarif.add(button_1)

# get ava free
keyboard_get_ava_free = InlineKeyboardMarkup(resize_keyboard=True, disable_notification=True)
button_1 = InlineKeyboardButton(text="Выбрать другой тариф", callback_data="Выбрать другой тариф")
keyboard_get_ava_free.add(
    *[
        button_1,
    ]
)



# вернуться в стейт выбора тарифа (из настроек)
keyboard_back_to_tarif = InlineKeyboardMarkup(resize_keyboard=True, row_width=1,disable_notification=True)
button_1 = InlineKeyboardButton(text=SEND_BACK_TO_TARIF, callback_data='SEND_BACK_TO_TARIF')
keyboard_back_to_tarif.add(button_1)

# инлайн кнопки в настройках
keyboard_settings = InlineKeyboardMarkup(resize_keyboard=True, disable_notification=True)
keyboard_settings.add(
    *[
        InlineKeyboardButton(
            text="Изменить гендер", callback_data="change_gender"
        ),
        InlineKeyboardButton(
            text="Загрузить новое фото", callback_data="change_own_photo"
        ),
    ]
)
keyboard_settings.add(
    InlineKeyboardButton(
        text="Поделиться реф. ссылкой с другом",
        switch_inline_query="change_own_photo",
    )
)



# инлайн кнопка 100 аватарок для админа
keyboard_admin_100_ava = InlineKeyboardMarkup(resize_keyboard=True, disable_notification=True)
keyboard_admin_100_ava.add(
    InlineKeyboardButton(
        text="Получить аватарки", callback_data="get_18+_avatarok"
    )
)
