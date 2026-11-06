import asyncio
import os
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal, User

from passlib.context import CryptContext

# Настраиваем схему шифрования (используем bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция 1: Превращает чистый пароль в хэш
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Функция 2: Сравнивает чистый пароль с хэшем из базы данных
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Автоматически создаем таблицы в базе данных, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Указываем FastAPI, что наши HTML-страницы лежат в папке templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Функция-помощник (Dependency) для открытия/закрытия сессии к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. ЭНДПОИНТ ДЛЯ ПОКАЗА СТРАНИЦЫ (GET-запрос)
# Когда пользователь просто переходит на http://127.0.0
@app.get("/", response_class=HTMLResponse)
def show_register_page(request: Request):
     return templates.TemplateResponse(request=request, name="register.html")

# 2. ЭНДПОИНТ ДЛЯ ОБРАБОТКИ ДАННЫХ ИЗ ФОРМЫ (POST-запрос)
# Когда пользователь нажимает кнопку "Зарегистрироваться"
@app.post("/register")
def handle_register(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Проверяем в PostgreSQL, нет ли уже пользователя с таким логином
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return "Ошибка: Пользователь с таким логином уже существует!"

    # Если всё ок — создаем нового пользователя
    # Хэшируем пароль перед сохранением
    hashed = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed)

    
    db.add(new_user)  # Добавляем в очередь на запись
    db.commit()      # Сохраняем в PostgreSQL намертво
        # Вместо текста отправляем пользователя на страницу входа
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def show_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/login")
def handle_login(
    request: Request,
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # 1. Ищем пользователя в базе данных
    user = db.query(User).filter(User.username == username).first()
    
    # 2. Если пользователя нет ИЛИ пароль не совпадает с хэшем
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    # 3. Передаем управление в Jinja2 и отрисовываем личный кабинет
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"username": username}
    )

# Тяжелая асинхронная задача для одного потока атаки
async def heavy_db_query():
    # Открываем отдельную сессию к БД для каждого потока атаки
    db = SessionLocal()
    try:
        # ВАЖНО: Мы используем .filter(User.username.like("%bot_user_999%"))
        # Поиск по подстроке с процентами в начале ОМЕНЯЕТ использование индексов в БД.
        # PostgreSQL будет вынужден перебрать ВСЕ 1 000 000 записей на диске для каждого запроса!
        result = db.query(User).filter(User.username.like("%bot_user_999%")).all()
        return len(result)
    finally:
        db.close()

# Эндпоинт, который вызывается при нажатии на Кнопку Атаки
@app.post("/trigger-attack")
async def trigger_attack():
    print("🔥 ВНИМАНИЕ: Запущена DoS-атака на базу данных PostgreSQL!")
    
    # Количество ОДНОВРЕМЕННЫХ тяжелых соединений к базе данных
    # Внимание: если у вас слабый ПК, начните с 30-50, чтобы система не намертво зависла
    CONCURRENT_ATTACKS = 50 
    
    start_time = asyncio.get_event_loop().time()
    
    # Создаем список из 50 параллельных задач
    tasks = [heavy_db_query() for _ in range(CONCURRENT_ATTACKS)]
    
    # Магия asyncio.gather: запускает все 50 тяжелых запросов в базу ОДНОВРЕМЕННО
    await asyncio.gather(*tasks)
    
    end_time = asyncio.get_event_loop().time()
    duration = round(end_time - start_time, 2)
    
    print(f"🛑 Атака завершена за {duration} сек. База обработала {CONCURRENT_ATTACKS} тяжелых сканирований.")
    
    return {"message": f"Атака успешно проведена! 50 тяжелых потоков перегружали базу в течение {duration} сек."}

