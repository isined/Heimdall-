from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Ссылка для подключения к базе данных.
DATABASE_URL = "postgresql+psycopg2://postgres:meowdg@localhost:5432/polygon_db"

# 2. Создаем движок (Engine) — ядро связи с Postgres
engine = create_engine(DATABASE_URL)

# 3. Фабрика сессий для отправки запросов
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Базовый класс для будущих таблиц
Base = declarative_base()


from sqlalchemy import Column, Integer, String

# Создаем модель для таблицы 'users'
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)