import sqlite3

# Создаем соединение с базой данных
conn = sqlite3.connect('data/example.db')
cursor = conn.cursor()

# Создаем таблицу products
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    productId TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    num_of_orders INTEGER NOT NULL,
    rating REAL NOT NULL
)
''')

# Заполняем таблицу 5 товарами категории электроника
products = [
    ('1', 'Смартфон XYZ', 'электроника', 19999.99, 150, 4.5),
    ('2', 'Ноутбук ABC', 'электроника', 59999.99, 75, 4.7),
    ('3', 'Наушники DEF', 'электроника', 2999.99, 200, 4.2),
    ('4', 'Телевизор GHI', 'электроника', 49999.99, 50, 4.6),
    ('5', 'Планшет JKL', 'электроника', 24999.99, 100, 4.3),
    ('6', 'Арбуз', 'ягоды', 100, 5000000, 5),
]

cursor.executemany('''
INSERT INTO products (productId, name, category, price, num_of_orders, rating)
VALUES (?, ?, ?, ?, ?, ?)
''', products)

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()
