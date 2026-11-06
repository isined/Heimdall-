import time
from database import SessionLocal, User
from main import get_password_hash  # Используем нашу функцию хэширования

def generate_bulk_data():
    db = SessionLocal()
    total_records = 1_000_000
    batch_size = 10_000  # Скидываем в базу пачками по 10 тысяч строк, чтобы не взорвать память
    
    print(f"🚀 Старт генерации {total_records} записей в PostgreSQL...")
    start_time = time.time()

    # Захешируем один дефолтный пароль заранее, чтобы не тратить ресурсы процессора на хэширование 1 млн раз
    dummy_password_hash = get_password_hash("password123")

    for i in range(1, total_records + 1):
        # Создаем мусорного пользователя
        user = User(
            username=f"bot_user_{i}",
            hashed_password=dummy_password_hash
        )
        db.add(user)

        # Каждые 10 000 записей делаем коммит в базу
        if i % batch_size == 0:
            db.commit()
            print(f"Записано: {i} / {total_records} пользователей...")

    db.close()
    end_time = time.time()
    print(f"🎉 Готово! 1 000 000 пользователей успешно созданы за {round(end_time - start_time, 2)} сек.")

if __name__ == "__main__":
    generate_bulk_data()
