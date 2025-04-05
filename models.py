from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import Column, BigInteger, DateTime, String, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
import asyncio

# Создание БД и подключение
DATABASE_URL = 'postgresql+asyncpg://postgres:1234qwerttest@45.81.243.111:5432/postgres'
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)

# Base - основной класс, с помощью него происходит управление всеми остальными классами (таблицами)
class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    users_name = Column(String, nullable=False)  # Имя пользователя
    users_id = Column(BigInteger, unique=True, nullable=False)  # Telegram ID пользователя

    # Связь с историей - один пользователь имеет много записей истории
    history = relationship("History", back_populates="user")


class History(Base):
    __tablename__ = 'history'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Добавляем ForeignKey, который ссылается на users_id из таблицы users
    telegram_id_users = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False)
    path_to_tz = Column(String, nullable=False)  # Путь к файлу ТЗ
    path_to_analyze = Column(String, nullable=False)  # Путь к файлу анализа

    # Связь с пользователем - каждая запись истории принадлежит одному пользователю
    user = relationship("User", back_populates="history")


# Функция, которая создаёт все вышеперечисленные таблицы
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def test_connection():
    try:
        async with engine.connect():
            print("Подключение успешно!")
    except Exception as e:
        print("Ошибка подключения:", str(e))
    finally:
        await engine.dispose()

# Основная асинхронная функция
async def async_main():
    await test_connection()  # Проверка подключения
    await create_tables()    # Создание таблиц

if __name__ == "__main__":
    asyncio.run(async_main())
