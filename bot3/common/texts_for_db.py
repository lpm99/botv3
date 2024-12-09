from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories = ['Фэнтези', 'Звери', 'Warhammer 40000', 'Монстры Лавкрафта']

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "about": "Мастерская Златолапа. Каждой принцессе нужен свой дракон",
    "payment": as_marked_section(
        Bold("Варианты оплаты:"),
        "Полная оплата производится после расчётов главного дракона😁",
        marker="✅ ",
    ).as_html(),
    "shipping": as_list(
        as_marked_section(
            Bold("Варианты доставки/заказа:"),
            "Доставка",
            "Самовывоз",
            "Почта",
            "Яндекс Доставка",
            "CDEK",
            marker="✅ ",
        ),
    ).as_html(),
    'catalog': 'Категории:',
    'cart': 'В корзине ничего нет!'
}
