import sqlite3

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

# Получаем средний возраст пользователей для каждого возраста
cursor.execute('SELECT * from messages')
results = cursor.fetchall()

for row in results:
  print(row)