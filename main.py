import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import io
import json
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import text  # ВАЖНО: Добавляем импорт text

# Настройка страницы
st.set_page_config(page_title="Учетная система автосалона", layout="wide")

# Система авторизации
VALID_USERS = {
    "manager1": "auto1111",
    "manager2": "auto1111",
    "manager3": "auto1111",
    "manager4": "auto1111",
    "leader": "alisher_krutoy"
}

def check_login(username, password):
    """Проверка логина и пароля"""
    return username in VALID_USERS and VALID_USERS[username] == password

def is_leader(username):
    """Проверка, является ли пользователь руководителем"""
    return username == "leader"

def get_user_role(username):
    """Получение роли пользователя"""
    if is_leader(username):
        return "👑 Руководитель"
    else:
        return "👤 Менеджер"

def login_form():
    """Форма входа в систему"""
    # Стилизованный заголовок
    st.markdown("""
    <div style="text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">🚗 AutoTrade</h1>
        <h2 style="color: white; margin: 10px 0;">Учетная система автосалона</h2>
        <p style="color: #e0e0e0; margin: 0;">Система управления автомобильными продажами</p>
        <hr style="border-color: rgba(255,255,255,0.3); margin: 20px 0;">
        <p style="margin: 0; color: white; font-size: 16px;">
            💻 Сделал <strong>Алишер Бейсембеков</strong>, основатель и разработчик<br>
            <small style="opacity: 0.8;">© 2025 AutoTrade - Система управления автосалоном</small>
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container():
            st.markdown("### 🔐 Авторизация менеджера")

            username = st.text_input("👤 Логин", placeholder="Введите ваш логин (manager1-4)")
            password = st.text_input("🔒 Пароль", type="password", placeholder="Введите пароль")

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button("🚀 Войти в систему", type="primary", use_container_width=True):
                    if check_login(username, password):
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.success(f"✅ Добро пожаловать, {username}!")
                        st.balloons()  # Праздничная анимация
                        st.rerun()
                    else:
                        st.error("❌ Неверный логин или пароль!")
                        st.warning("💡 Проверьте правильность ввода данных")

            st.markdown("---")

            # Информационная панель
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">
                <h4 style="margin-top: 0;">ℹ️ Информация для входа</h4>
                <p><strong>Менеджеры:</strong> manager1, manager2, manager3, manager4</p>
                <p><strong>Руководитель:</strong> leader</p>
                <p><strong>Пароли:</strong> у каждой роли свой пароль</p>
                <p><small>При проблемах со входом обратитесь к администратору системы</small></p>
            </div>
            """, unsafe_allow_html=True)

def logout():
    """Выход из системы"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.rerun()

# Проверка авторизации
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_form()
    st.stop()

# Если пользователь авторизован, показываем основное приложение

# Конфигурация машин и цен
CAR_TYPES = {
    "ГИБРИД 150К": 150000,
    "ГИБРИД 250К": 250000,
    "ГИБРИД 300К": 300000,
    "ДВС 70К": 70000,
    "БУУ АВТО 50К": 50000
}

# Цвета для типов машин
CAR_TYPE_COLORS = {
    "ГИБРИД 150К": "4472C4",
    "ГИБРИД 250К": "C5504B",
    "ГИБРИД 300К": "70AD47",
    "ДВС 70К": "FFC000",
    "БУУ АВТО 50К": "7030A0"
}

# Предустановленные автосалоны (полный список партнеров)
DEFAULT_DEALERSHIPS = [
    "EL MOTORS",
    "LID CAR",
    "URBAN AUTO",
    "SAKURA MOTORS",
    "DREAM CAR",
    "NEW CAR/BOSS CAR",
    "CARMAX",
    "LYNG GO",
    "REAL AUTO ALMATY",
    "BOSSCAR",
    "GALAXY AVTO CENTER",
    "AST MOTORS",
    "ARB KAZAKHSTAN",
    "LYNK&CO AUTOINVEST",
    "ALMATY AUTO MOTORS",
    "HALYK AUTO",
    "СООРУЖЕНИЕ",
    "EV MASTER",
    "CHANGAN AUTO ALMATY",
    "DREAM CAR MARKET",
    "MIX AUTO",
    "MIR AUTO",
    "RAMADA AUTOMARKET",
    "SILK ROAD AUTO",
    "AVTOSHOPPING02",
    "CHINACARS",
    "ES MOTORS",
    "Q4TULPAR",
    "AVTOMARKET",
    "UCAR",
    "AUTO_CENTER_KZ",
    "ZENITH AUTO & DETAILING",
    "REGIONAUTOKZ"
]

# Инициализация PostgreSQL подключения
@st.cache_resource
def init_database():
    """Инициализация PostgreSQL базы данных"""
    try:
        # Создаем подключение к PostgreSQL
        conn = st.connection("postgresql", type="sql")
        
        # Для DDL операций используем прямое подключение к движку
        engine = conn._instance
        
        # Создание таблиц
        with engine.connect() as connection:
            # ВАЖНО: Используем text() для SQL запросов
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS dealerships (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS cars (
                    id SERIAL PRIMARY KEY,
                    dealership_id INTEGER REFERENCES dealerships(id),
                    car_type VARCHAR(100) NOT NULL,
                    count INTEGER NOT NULL,
                    price_per_car INTEGER NOT NULL,
                    total_amount INTEGER NOT NULL,
                    date_added DATE NOT NULL,
                    is_paid BOOLEAN DEFAULT FALSE,
                    payment_date DATE,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            connection.commit()
        
        # Добавляем базовые автосалоны если их нет
        try:
            existing_dealerships = conn.query("SELECT name FROM dealerships", ttl=0)
            existing_names = existing_dealerships['name'].tolist() if not existing_dealerships.empty else []
        except:
            existing_names = []
        
        # Добавляем отсутствующие автосалоны
        with engine.connect() as connection:
            for dealership in DEFAULT_DEALERSHIPS:
                if dealership not in existing_names:
                    connection.execute(
                        text("INSERT INTO dealerships (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                        {"name": dealership}
                    )
            connection.commit()
        
        return conn
        
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        st.info("Проверьте настройки PostgreSQL в secrets")
        st.stop()

# Функции для работы с БД
def get_dealerships(conn):
    """Получение списка автосалонов"""
    result = conn.query("SELECT id, name FROM dealerships ORDER BY name", ttl=0)
    return [(row.id, row.name) for _, row in result.iterrows()]

def add_dealership(conn, name):
    """Добавление нового автосалона"""
    try:
        engine = conn._instance
        with engine.connect() as connection:
            connection.execute(
                text("INSERT INTO dealerships (name) VALUES (:name)"),
                {"name": name}
            )
            connection.commit()
        return True
    except Exception:
        return False

def can_add_cars_for_dealership(conn, dealership_id, target_date):
    """Все автосалоны могут добавлять машины без предоплаты"""
    return True

def add_car_entry(conn, dealership_id, car_type, count, date_added, is_paid=False):
    """Добавление записи о машинах"""
    price_per_car = CAR_TYPES[car_type]
    total_amount = price_per_car * count
    current_user = st.session_state.get('current_user', 'unknown')
    
    # Если машины отмечены как оплаченные при добавлении, ставим дату оплаты
    payment_date = date.today() if is_paid else None
    updated_by = current_user if is_paid else None
    
    engine = conn._instance
    with engine.connect() as connection:
        connection.execute(text('''
            INSERT INTO cars (dealership_id, car_type, count, price_per_car, total_amount, 
                             date_added, is_paid, payment_date, created_by, updated_by)
            VALUES (:dealership_id, :car_type, :count, :price_per_car, :total_amount,
                    :date_added, :is_paid, :payment_date, :created_by, :updated_by)
        '''), {
            "dealership_id": dealership_id,
            "car_type": car_type,
            "count": count,
            "price_per_car": price_per_car,
            "total_amount": total_amount,
            "date_added": date_added,
            "is_paid": is_paid,
            "payment_date": payment_date,
            "created_by": current_user,
            "updated_by": updated_by
        })
        connection.commit()

def update_car_payment_status(conn, car_id, is_paid):
    """Обновление статуса оплаты"""
    current_user = st.session_state.get('current_user', 'unknown')
    payment_date = date.today() if is_paid else None
    
    engine = conn._instance
    with engine.connect() as connection:
        connection.execute(text('''
            UPDATE cars 
            SET is_paid = :is_paid, payment_date = :payment_date, updated_by = :updated_by
            WHERE id = :car_id
        '''), {
            "is_paid": is_paid,
            "payment_date": payment_date,
            "updated_by": current_user,
            "car_id": car_id
        })
        connection.commit()

def get_car_payment_status_for_today(conn, car_id):
    """Проверяет статус оплаты машины на сегодня"""
    result = conn.query('''
        SELECT is_paid, payment_date
        FROM cars
        WHERE id = :car_id
    ''', params={"car_id": car_id}, ttl=0)
    
    if result.empty:
        return False
    
    row = result.iloc[0]
    if not row.is_paid or pd.isna(row.payment_date):
        return False
    
    # Проверяем, что оплата была сегодня
    payment_date = pd.to_datetime(row.payment_date).date()
    return payment_date == date.today()

def get_cars_by_month_dealership(conn, year, month, dealership_id=None):
    """Получение машин за месяц по автосалонам"""
    query = '''
        SELECT c.*, d.name as dealership_name
        FROM cars c
        JOIN dealerships d ON c.dealership_id = d.id
        WHERE EXTRACT(year FROM c.date_added) = :year 
        AND EXTRACT(month FROM c.date_added) = :month
    '''
    params = {"year": year, "month": month}
    
    if dealership_id:
        query += ' AND c.dealership_id = :dealership_id'
        params["dealership_id"] = dealership_id
    
    query += ' ORDER BY d.name, c.date_added'
    
    result = conn.query(query, params=params, ttl=0)
    return [tuple(row) for _, row in result.iterrows()]

def get_monthly_summary(conn, year, month):
    """Получение сводки за месяц"""
    result = conn.query('''
        SELECT d.name as dealership_name,
               c.car_type,
               SUM(c.count) as total_count,
               SUM(c.total_amount) as total_amount,
               SUM(CASE WHEN c.is_paid THEN c.count ELSE 0 END) as paid_count,
               COUNT(CASE WHEN c.is_paid THEN 1 END) as paid_entries
        FROM cars c
        JOIN dealerships d ON c.dealership_id = d.id
        WHERE EXTRACT(year FROM c.date_added) = :year
        AND EXTRACT(month FROM c.date_added) = :month
        GROUP BY d.id, d.name, c.car_type
        ORDER BY d.name, c.car_type
    ''', params={"year": year, "month": month}, ttl=0)
    
    return [tuple(row) for _, row in result.iterrows()]

def get_cars_by_day(conn, year, month, dealership_name, car_type):
    """Получение машин по дням месяца"""
    result = conn.query('''
        SELECT EXTRACT(day FROM c.date_added) as day,
               SUM(c.count) as total_count
        FROM cars c
        JOIN dealerships d ON c.dealership_id = d.id
        WHERE EXTRACT(year FROM c.date_added) = :year
        AND EXTRACT(month FROM c.date_added) = :month
        AND d.name = :dealership_name
        AND c.car_type = :car_type
        GROUP BY EXTRACT(day FROM c.date_added)
    ''', params={
        "year": year, 
        "month": month, 
        "dealership_name": dealership_name, 
        "car_type": car_type
    }, ttl=0)
    
    result_dict = {}
    for _, row in result.iterrows():
        day = int(row.day)
        count = row.total_count
        result_dict[day] = count
    
    return result_dict

# Функция создания улучшенного Excel отчета
def create_excel_report(conn, year, month):
    wb = Workbook()
    ws = wb.active
    ws.title = f"Отчет {calendar.month_name[month]} {year}"

    # Стили
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    paid_fill = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")
    unpaid_fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
    dealership_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")

    header_font = Font(color="FFFFFF", bold=True)
    bold_font = Font(bold=True)
    center_alignment = Alignment(horizontal="center", vertical="center")

    # Заголовки статуса
    ws['C1'] = "ОТПРАВЛЕН СЧЕТ"
    ws['C1'].fill = unpaid_fill
    ws['C2'] = "СЧЕТ ОПЛАЧЕН"
    ws['C2'].fill = paid_fill

    # Заголовок таблицы
    ws['M3'] = "ТАБЛИЦА ОТЧЕТА AutoTrade"
    ws['M3'].font = header_font
    ws['M3'].fill = header_fill
    ws['M3'].alignment = center_alignment
    ws.merge_cells('M3:S3')

    # Заголовки столбцов
    ws['A4'] = "АВТОСАЛОН"
    ws['A4'].fill = dealership_fill
    ws['A4'].font = bold_font
    ws['A4'].alignment = center_alignment

    ws['B4'] = "ТИП МАШИНЫ"
    ws['B4'].fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    ws['B4'].font = Font(color="FFFFFF", bold=True)
    ws['B4'].alignment = center_alignment

    # Числа месяца
    days_in_month = calendar.monthrange(year, month)[1]
    for day in range(1, days_in_month + 1):
        col = get_column_letter(3 + day - 1)
        ws[f'{col}4'] = day
        ws[f'{col}4'].fill = PatternFill(start_color="9BC2E6", end_color="9BC2E6", fill_type="solid")
        ws[f'{col}4'].alignment = center_alignment
        ws[f'{col}4'].font = bold_font

    # Колонки итогов
    total_col = get_column_letter(3 + days_in_month)
    paid_col = get_column_letter(3 + days_in_month + 1)

    ws[f'{total_col}4'] = "ВСЕГО"
    ws[f'{total_col}4'].fill = PatternFill(start_color="C5504B", end_color="C5504B", fill_type="solid")
    ws[f'{total_col}4'].font = Font(color="FFFFFF", bold=True)
    ws[f'{total_col}4'].alignment = center_alignment

    ws[f'{paid_col}4'] = "ОПЛАЧЕНО"
    ws[f'{paid_col}4'].fill = paid_fill
    ws[f'{paid_col}4'].font = Font(color="FFFFFF", bold=True)
    ws[f'{paid_col}4'].alignment = center_alignment

    # Получаем данные
    summary_data = get_monthly_summary(conn, year, month)
    current_row = 5

    # Группируем по автосалонам
    dealership_groups = {}
    for row in summary_data:
        dealership = row[0]
        if dealership not in dealership_groups:
            dealership_groups[dealership] = []
        dealership_groups[dealership].append(row)

    # Заполняем данные
    for dealership, types in dealership_groups.items():
        # Объединяем ячейки для автосалона
        start_row = current_row
        end_row = current_row + len(types) - 1

        if len(types) > 1:
            ws.merge_cells(f'A{start_row}:A{end_row}')

        ws[f'A{start_row}'] = dealership
        ws[f'A{start_row}'].fill = dealership_fill
        ws[f'A{start_row}'].font = Font(color="FFFFFF", bold=True)
        ws[f'A{start_row}'].alignment = center_alignment

        # Заполняем типы машин
        for car_data in types:
            _, car_type, total_count, total_amount, paid_count, _ = car_data

            # Тип машины
            ws[f'B{current_row}'] = car_type
            car_color = CAR_TYPE_COLORS.get(car_type, "808080")
            ws[f'B{current_row}'].fill = PatternFill(start_color=car_color, end_color=car_color, fill_type="solid")
            ws[f'B{current_row}'].font = Font(color="FFFFFF", bold=True)
            ws[f'B{current_row}'].alignment = center_alignment

            # Заполняем данные по дням
            cars_by_day = get_cars_by_day(conn, year, month, dealership, car_type)
            for day, count in cars_by_day.items():
                col = get_column_letter(3 + day - 1)
                ws[f'{col}{current_row}'] = count
                ws[f'{col}{current_row}'].alignment = center_alignment

            # Итоги
            ws[f'{total_col}{current_row}'] = total_count
            ws[f'{total_col}{current_row}'].alignment = center_alignment
            ws[f'{total_col}{current_row}'].font = bold_font

            ws[f'{paid_col}{current_row}'] = paid_count
            ws[f'{paid_col}{current_row}'].alignment = center_alignment
            if paid_count == total_count and total_count > 0:
                ws[f'{paid_col}{current_row}'].fill = paid_fill
            elif paid_count > 0:
                ws[f'{paid_col}{current_row}'].fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")

            current_row += 1

        current_row += 1  # Пропуск строки между автосалонами

    # Легенда типов машин
    legend_row = current_row + 2
    ws[f'A{legend_row}'] = "ЛЕГЕНДА ТИПОВ МАШИН:"
    ws[f'A{legend_row}'].font = bold_font

    legend_row += 1
    for idx, (car_type, price) in enumerate(CAR_TYPES.items()):
        col = get_column_letter(1 + idx)
        ws[f'{col}{legend_row}'] = f"{car_type} ({price:,} тг)"
        car_color = CAR_TYPE_COLORS.get(car_type, "808080")
        ws[f'{col}{legend_row}'].fill = PatternFill(start_color=car_color, end_color=car_color, fill_type="solid")
        ws[f'{col}{legend_row}'].font = Font(color="FFFFFF", bold=True)
        ws[f'{col}{legend_row}'].alignment = center_alignment

    return wb

# Инициализация БД
conn = init_database()

# Инициализация session state
if 'excel_reports' not in st.session_state:
    st.session_state.excel_reports = {}

if 'expanded_sections' not in st.session_state:
    st.session_state.expanded_sections = {}

# Инициализация режима группировки
if 'view_mode' not in st.session_state:
    current_user = st.session_state.get('current_user', 'unknown')
    st.session_state.view_mode = "По дням" if is_leader(current_user) else "По автосалонам"

# Заголовок с информацией о пользователе
header_col1, header_col2, header_col3 = st.columns([2, 2, 1])

with header_col1:
    st.title("🚗 Учетная система автосалона AutoTrade")

with header_col2:
    current_user = st.session_state.get('current_user', 'Неизвестно')
    user_role = get_user_role(current_user)
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <h4>{user_role}: {current_user}</h4>
        <p>📅 {date.today().strftime('%d.%m.%Y')}</p>
    </div>
    """, unsafe_allow_html=True)

with header_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Выйти", type="secondary", help="Выход из системы"):
        logout()

st.divider()

# Боковая панель
with st.sidebar:
    # Информация о пользователе
    current_user = st.session_state.get('current_user', 'Неизвестно')
    user_role = get_user_role(current_user)
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <h4 style="margin: 0;">{user_role}</h4>
        <p style="margin: 0; font-size: 14px;"><strong>{current_user}</strong></p>
        <p style="margin: 0; font-size: 12px;">Активная сессия</p>
    </div>
    """, unsafe_allow_html=True)

    # Функции для руководителя
    if is_leader(current_user):
        st.header("🏢 Управление автосалонами")

        # Показываем общее количество автосалонов
        total_dealerships = len(get_dealerships(conn))
        st.info(f"📊 Всего автосалонов в системе: **{total_dealerships}**")

        # Добавление нового автосалона (только для руководителя)
        new_dealership = st.text_input("Новый автосалон")
        if st.button("Добавить автосалон"):
            if new_dealership:
                if add_dealership(conn, new_dealership):
                    st.success(f"✅ Добавлен автосалон: {new_dealership}")
                    st.rerun()
                else:
                    st.error("❌ Такой автосалон уже существует")

        st.divider()

        # Аналитика руководителя
        st.header("📊 Административная панель")

        # Общая статистика системы
        total_stats_result = conn.query('SELECT SUM(count), SUM(total_amount) FROM cars', ttl=0)
        
        if not total_stats_result.empty and not pd.isna(total_stats_result.iloc[0, 0]):
            total_cars = int(total_stats_result.iloc[0, 0])
            total_amount = int(total_stats_result.iloc[0, 1])
            
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.metric("Всего машин", total_cars)
            with col_a2:
                st.metric("Общий оборот", f"{total_amount:,} тг")

            # Статистика по оплатам
            paid_cars_result = conn.query('SELECT SUM(count) FROM cars WHERE is_paid = TRUE', ttl=0)
            paid_cars = int(paid_cars_result.iloc[0, 0]) if not paid_cars_result.empty and not pd.isna(paid_cars_result.iloc[0, 0]) else 0

            if total_cars > 0:
                payment_rate = (paid_cars / total_cars) * 100
                st.metric("Процент оплат", f"{payment_rate:.1f}%")

        st.divider()

        # Детальная статистика по менеджерам
        st.header("👥 Активность менеджеров")

        manager_stats_result = conn.query('''
            SELECT created_by,
                   COUNT(*) as entries_count,
                   SUM(count) as total_cars,
                   SUM(total_amount) as total_amount,
                   SUM(CASE WHEN is_paid THEN count ELSE 0 END) as paid_cars
            FROM cars
            WHERE created_by IS NOT NULL
            AND created_by != 'unknown'
            GROUP BY created_by
            ORDER BY SUM(count) DESC
        ''', ttl=0)

        if not manager_stats_result.empty:
            for _, row in manager_stats_result.iterrows():
                manager = row.created_by
                entries = int(row.entries_count)
                cars_count = int(row.total_cars)
                total_amount = int(row.total_amount)
                paid_cars = int(row.paid_cars)
                
                # Статистика по обработанным оплатам
                processed_result = conn.query(
                    'SELECT SUM(count) FROM cars WHERE updated_by = :manager AND is_paid = TRUE',
                    params={"manager": manager},
                    ttl=0
                )
                processed_payments = int(processed_result.iloc[0, 0]) if not processed_result.empty and not pd.isna(processed_result.iloc[0, 0]) else 0

                efficiency = (paid_cars / cars_count * 100) if cars_count > 0 else 0

                with st.expander(f"📊 {manager} ({cars_count} машин)", expanded=False):
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Записей", entries)
                        st.metric("Машин добавил", cars_count)
                    with col_m2:
                        st.metric("На сумму", f"{total_amount:,} тг")
                        st.metric("Оплачено машин", f"{paid_cars}/{cars_count}")
                    with col_m3:
                        st.metric("Обработал оплат", processed_payments)
                        st.metric("Эффективность", f"{efficiency:.1f}%")
        else:
            st.info("Статистика появится после работы менеджеров")

    # Функции для менеджеров
    else:
        st.header("Добавить машину")

        # Выбор автосалона
        dealerships = get_dealerships(conn)
        dealership_dict = {name: id for id, name in dealerships}
        selected_dealership_name = st.selectbox("Автосалон", list(dealership_dict.keys()))
        selected_dealership_id = dealership_dict.get(selected_dealership_name)

        # Выбор даты
        selected_date = st.date_input("Дата добавления", value=date.today())

        # Выбор типа машины
        car_type = st.selectbox("Тип машины", list(CAR_TYPES.keys()))

        # Количество машин
        car_count = st.number_input("Количество машин", min_value=1, value=1)

        # Статус оплаты
        is_paid = st.checkbox("Машины оплачены", value=False, help="Отметьте если машины уже оплачены клиентом")

        # Кнопка добавления
        if st.button("Добавить машины"):
            add_car_entry(conn, selected_dealership_id, car_type, car_count, selected_date, is_paid)
            status = "оплаченных" if is_paid else "неоплаченных"
            st.success(f"✅ Добавлено {car_count} {status} машин типа {car_type} для {selected_dealership_name}")
            st.rerun()

        st.divider()

        # Статистика по текущему менеджеру
        st.subheader("📈 Ваша статистика")

        user_stats_result = conn.query(
            'SELECT SUM(count), SUM(total_amount) FROM cars WHERE created_by = :user',
            params={"user": current_user},
            ttl=0
        )

        if not user_stats_result.empty and not pd.isna(user_stats_result.iloc[0, 0]):
            user_cars = int(user_stats_result.iloc[0, 0])
            user_amount = int(user_stats_result.iloc[0, 1])
            st.metric("Добавлено машин", user_cars)
            st.metric("На сумму", f"{user_amount:,} тг")
        else:
            st.info("Вы еще не добавляли машины")

        # Статистика по оплатам
        user_payments_result = conn.query(
            'SELECT SUM(count) FROM cars WHERE updated_by = :user AND is_paid = TRUE',
            params={"user": current_user},
            ttl=0
        )
        user_payments = int(user_payments_result.iloc[0, 0]) if not user_payments_result.empty and not pd.isna(user_payments_result.iloc[0, 0]) else 0

        if user_payments > 0:
            st.metric("Обработано оплат", f"{user_payments} машин")

    st.divider()

    # Кнопка выхода
    if st.button("🚪 Выйти из системы", type="secondary", use_container_width=True):
        logout()

# Основной контент
col1, col2 = st.columns([3, 1])

with col1:
    st.header("📊 Учет по месяцам и автосалонам")

    # Выбор месяца для просмотра
    view_col1, view_col2, view_col3, view_col4 = st.columns([2, 2, 2, 1])
    with view_col1:
        view_year = st.selectbox("Год для просмотра", range(2023, 2030), index=2)
    with view_col2:
        view_month = st.selectbox("Месяц для просмотра", range(1, 13), index=date.today().month - 1)
    with view_col3:
        # Используем сохраненный режим группировки из session state
        view_mode_options = ["По автосалонам", "По дням"]
        current_index = view_mode_options.index(st.session_state.view_mode)

        selected_mode = st.selectbox("Группировка", view_mode_options, index=current_index)

        # Обновляем session state при изменении
        if selected_mode != st.session_state.view_mode:
            st.session_state.view_mode = selected_mode
            st.rerun()

        view_mode = st.session_state.view_mode

    with view_col4:
        if st.button("🔄 Обновить все", help="Обновить статус всех оплат"):
            st.rerun()

    month_name = calendar.month_name[view_month]

    # Получаем данные за месяц
    cars_data = get_cars_by_month_dealership(conn, view_year, view_month)

    if cars_data:
        st.subheader(f"📅 {month_name} {view_year}")

        if view_mode == "По дням":
            # Группировка по дням
            day_groups = {}
            for car in cars_data:
                car_date = str(car[6])  # date_added
                if car_date not in day_groups:
                    day_groups[car_date] = []
                day_groups[car_date].append(car)

            # Сортируем дни по убыванию (последние дни сверху)
            sorted_days = sorted(day_groups.keys(), reverse=True)

            for car_date in sorted_days:
                cars = day_groups[car_date]

                # Парсим дату для красивого отображения
                date_obj = datetime.strptime(str(car_date), '%Y-%m-%d').date()
                day_name = date_obj.strftime('%d %B %Y (%A)')

                # Подсчитываем итоги за день
                day_total_cars = sum(car[3] for car in cars)  # count
                day_total_amount = sum(car[5] for car in cars)  # total_amount
                day_paid_cars = sum(car[3] for car in cars if get_car_payment_status_for_today(conn, car[0]) or car[7])

                # Цвет в зависимости от даты
                if date_obj == date.today():
                    bg_color = "#e8f5e8"  # Светло-зеленый для сегодня
                    day_emoji = "📅"
                elif date_obj == date.today() - timedelta(days=1):
                    bg_color = "#fff3e0"  # Светло-оранжевый для вчера
                    day_emoji = "📋"
                else:
                    bg_color = "#f8f9fa"  # Обычный для остальных
                    day_emoji = "📄"

                with st.container():
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>{day_emoji} {day_name}</h4>
                        <p>Машин: {day_total_cars} | Сумма: {day_total_amount:,} тг | Оплачено: {day_paid_cars}/{day_total_cars}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Группируем по автосалонам внутри дня
                    day_dealership_groups = {}
                    for car in cars:
                        dealership = car[12]  # dealership_name
                        if dealership not in day_dealership_groups:
                            day_dealership_groups[dealership] = []
                        day_dealership_groups[dealership].append(car)

                    for dealership, dealership_cars in day_dealership_groups.items():
                        with st.expander(f"🏢 {dealership} ({len(dealership_cars)} записей)", expanded=False):

                            # Отображаем машины
                            for car in dealership_cars:
                                car_id, dealership_id, car_type, count, price_per_car, total_amount, date_added, is_paid, payment_date, created_by, updated_by, created_at, dealership_name = car

                                # Проверяем статус оплаты на сегодня (свежий запрос из БД)
                                paid_today = get_car_payment_status_for_today(conn, car_id)

                                # Цвет статуса оплаты
                                if paid_today:
                                    status_color = "🟢"
                                    status_text = f"Оплачено сегодня ({updated_by or 'N/A'})" if updated_by else "Оплачено сегодня"
                                elif is_paid:
                                    status_color = "🟡"
                                    payment_info = f" ({updated_by})" if updated_by else ""
                                    status_text = f"Оплачено {payment_date}{payment_info}" if payment_date else f"Оплачено ранее{payment_info}"
                                else:
                                    status_color = "🔴"
                                    status_text = "Не оплачено"

                                car_col1, car_col2, car_col3, car_col4 = st.columns([2, 1, 1, 1])

                                with car_col1:
                                    creator_info = f" (добавил: {created_by})" if created_by else ""
                                    st.write(f"**{car_type}** - {count} шт.{creator_info}")
                                with car_col2:
                                    st.write(f"{total_amount:,} тг")
                                with car_col3:
                                    st.write(f"{status_color} {status_text}")
                                with car_col4:
                                    # Кнопка переключения оплаты
                                    button_key = f"payment_btn_{car_id}_{date.today()}_{car_date}"

                                    if paid_today:
                                        if st.button("❌ Отменить оплату", key=f"unpay_{button_key}", type="secondary"):
                                            update_car_payment_status(conn, car_id, False)
                                            st.success("✅ Оплата отменена!")
                                            st.rerun()
                                    else:
                                        if st.button("✅ Оплатить сегодня", key=f"pay_{button_key}", type="primary"):
                                            update_car_payment_status(conn, car_id, True)
                                            st.success("✅ Оплата зарегистрирована на сегодня!")
                                            st.rerun()

        else:
            # Старая группировка по автосалонам
            # Группируем по автосалонам
            dealership_groups = {}
            for car in cars_data:
                dealership = car[12]  # dealership_name
                if dealership not in dealership_groups:
                    dealership_groups[dealership] = []
                dealership_groups[dealership].append(car)

            # Отображаем по автосалонам
            for dealership, cars in dealership_groups.items():

                # Добавляем кнопку обновления для каждого автосалона
                dealership_col1, dealership_col2 = st.columns([3, 1])

                with dealership_col2:
                    if st.button("🔄 Обновить", key=f"refresh_{dealership}_{view_year}_{view_month}",
                                 help="Обновить статус оплат"):
                        st.rerun()

                with st.expander(f"🏢 {dealership}", expanded=True):

                    # Отображаем машины
                    for car in cars:
                        car_id, dealership_id, car_type, count, price_per_car, total_amount, date_added, is_paid, payment_date, created_by, updated_by, created_at, dealership_name = car

                        # Проверяем статус оплаты на сегодня (свежий запрос из БД)
                        paid_today = get_car_payment_status_for_today(conn, car_id)

                        # Цвет статуса оплаты
                        if paid_today:
                            status_color = "🟢"
                            status_text = f"Оплачено сегодня ({updated_by or 'N/A'})" if updated_by else "Оплачено сегодня"
                        elif is_paid:
                            status_color = "🟡"
                            payment_info = f" ({updated_by})" if updated_by else ""
                            status_text = f"Оплачено {payment_date}{payment_info}" if payment_date else f"Оплачено ранее{payment_info}"
                        else:
                            status_color = "🔴"
                            status_text = "Не оплачено"

                        car_col1, car_col2, car_col3, car_col4 = st.columns([2, 1, 1, 1])

                        with car_col1:
                            creator_info = f" (добавил: {created_by})" if created_by else ""
                            st.write(f"**{car_type}** - {count} шт. ({date_added}){creator_info}")
                        with car_col2:
                            st.write(f"{total_amount:,} тг")
                        with car_col3:
                            st.write(f"{status_color} {status_text}")
                        with car_col4:
                            # Кнопка переключения оплаты (только одна кнопка в зависимости от статуса)
                            button_key = f"payment_btn_{car_id}_{date.today()}_{view_year}_{view_month}"

                            if paid_today:
                                # Если оплачено сегодня - показываем кнопку отмены
                                if st.button("❌ Отменить оплату", key=f"unpay_{button_key}", type="secondary"):
                                    update_car_payment_status(conn, car_id, False)
                                    st.success("✅ Оплата отменена!")
                                    # Принудительное обновление интерфейса
                                    st.rerun()
                            else:
                                # Если не оплачено сегодня - показываем кнопку оплаты
                                if st.button("✅ Оплатить сегодня", key=f"pay_{button_key}", type="primary"):
                                    update_car_payment_status(conn, car_id, True)
                                    st.success("✅ Оплата зарегистрирована на сегодня!")
                                    # Принудительное обновление интерфейса
                                    st.rerun()

                    # Итоги по автосалону
                    dealership_total = sum(car[5] for car in cars)  # total_amount
                    dealership_cars = sum(car[3] for car in cars)  # count
                    paid_cars_today = sum(car[3] for car in cars if get_car_payment_status_for_today(conn, car[0]))

                    st.markdown("---")
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    with summary_col1:
                        st.metric("Всего машин", dealership_cars)
                    with summary_col2:
                        st.metric("Оплачено сегодня", f"{paid_cars_today}/{dealership_cars}")
                    with summary_col3:
                        st.metric("Сумма", f"{dealership_total:,} тг")

        # Кнопка экспорта
        st.divider()

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            if st.button(f"📊 Создать отчет Excel", key=f"create_excel_{view_year}_{view_month}"):
                wb = create_excel_report(conn, view_year, view_month)

                excel_buffer = io.BytesIO()
                wb.save(excel_buffer)
                excel_buffer.seek(0)

                # Сохраняем в session state для скачивания
                st.session_state[f'excel_data_{view_year}_{view_month}'] = excel_buffer.getvalue()
                st.success("✅ Отчет создан! Нажмите кнопку скачивания справа.")

        with export_col2:
            # Кнопка скачивания (активна только после создания отчета)
            excel_key = f'excel_data_{view_year}_{view_month}'
            if excel_key in st.session_state:
                st.download_button(
                    label=f"💾 Скачать отчет {month_name} {view_year}.xlsx",
                    data=st.session_state[excel_key],
                    file_name=f"Отчет_{month_name}_{view_year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{view_year}_{view_month}"
                )
            else:
                st.button("💾 Сначала создайте отчет", disabled=True)

    else:
        st.info(f"Данные за {month_name} {view_year} отсутствуют.")

with col2:
    if is_leader(current_user):
        st.header("👑 Панель руководителя")

        # Расширенная аналитика для руководителя
        total_stats_result = conn.query('SELECT SUM(count), SUM(total_amount) FROM cars', ttl=0)

        if not total_stats_result.empty and not pd.isna(total_stats_result.iloc[0, 0]):
            # Основные KPI
            st.subheader("🎯 Ключевые показатели")

            total_cars = int(total_stats_result.iloc[0, 0])
            total_revenue = int(total_stats_result.iloc[0, 1])

            paid_cars_result = conn.query('SELECT SUM(count) FROM cars WHERE is_paid = TRUE', ttl=0)
            paid_cars = int(paid_cars_result.iloc[0, 0]) if not paid_cars_result.empty and not pd.isna(paid_cars_result.iloc[0, 0]) else 0

            paid_revenue_result = conn.query('SELECT SUM(total_amount) FROM cars WHERE is_paid = TRUE', ttl=0)
            paid_revenue = int(paid_revenue_result.iloc[0, 0]) if not paid_revenue_result.empty and not pd.isna(paid_revenue_result.iloc[0, 0]) else 0

            col_kpi1, col_kpi2 = st.columns(2)
            with col_kpi1:
                st.metric("💰 Получено", f"{paid_revenue:,} тг")
                st.metric("🚗 Оплачено машин", f"{paid_cars}/{total_cars}")
            with col_kpi2:
                pending_revenue = total_revenue - paid_revenue
                st.metric("⏳ Ожидается", f"{pending_revenue:,} тг")
                payment_rate = (paid_cars / total_cars * 100) if total_cars > 0 else 0
                st.metric("📊 Конверсия", f"{payment_rate:.1f}%")

            # Прогресс бар
            st.progress(payment_rate / 100, text=f"Выполнение плана: {payment_rate:.1f}%")

            st.divider()

            # График динамики продаж
            st.subheader("📈 Динамика продаж")

            daily_data_result = conn.query('''
                SELECT date_added,
                       SUM(count) as daily_cars,
                       SUM(total_amount) as daily_revenue,
                       SUM(CASE WHEN is_paid THEN total_amount ELSE 0 END) as daily_paid
                FROM cars
                WHERE date_added >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY date_added
                ORDER BY date_added
            ''', ttl=0)

            if not daily_data_result.empty:
                dates = daily_data_result['date_added'].tolist()
                cars_data = daily_data_result['daily_cars'].tolist()
                revenue_data = daily_data_result['daily_revenue'].tolist()
                paid_data = daily_data_result['daily_paid'].tolist()

                # График машин по дням
                chart_data = pd.DataFrame({
                    'Дата': dates,
                    'Добавлено машин': cars_data,
                    'Оборот (тыс. тг)': [x / 1000 for x in revenue_data],
                    'Получено (тыс. тг)': [x / 1000 for x in paid_data]
                })

                st.line_chart(chart_data.set_index('Дата'))

            st.divider()

            # Аналитика по типам машин
            st.subheader("🚗 Популярность типов машин")

            car_types_result = conn.query('''
                SELECT car_type,
                       SUM(count) as total_count,
                       SUM(total_amount) as total_amount,
                       SUM(CASE WHEN is_paid THEN count ELSE 0 END) as paid_count
                FROM cars
                GROUP BY car_type
                ORDER BY SUM(count) DESC
            ''', ttl=0)

            if not car_types_result.empty:
                # Создаем данные для графика
                types_chart = pd.DataFrame({
                    'Тип машины': car_types_result['car_type'].tolist(),
                    'Продано': car_types_result['total_count'].tolist(),
                    'Оплачено': car_types_result['paid_count'].tolist()
                })

                st.bar_chart(types_chart.set_index('Тип машины'))

                # Детальная таблица
                for _, row in car_types_result.iterrows():
                    car_type = row.car_type
                    total_count = int(row.total_count)
                    total_amount = int(row.total_amount)
                    paid_count = int(row.paid_count)
                    conversion = (paid_count / total_count * 100) if total_count > 0 else 0
                    
                    with st.expander(f"🚙 {car_type}: {total_count} шт.", expanded=False):
                        col_ct1, col_ct2, col_ct3 = st.columns(3)
                        with col_ct1:
                            st.metric("Всего", total_count)
                        with col_ct2:
                            st.metric("Оплачено", f"{paid_count}/{total_count}")
                        with col_ct3:
                            st.metric("Конверсия", f"{conversion:.1f}%")

        else:
            st.info("📈 Аналитика появится после начала работы")

    else:
        # Упрощенная панель для менеджеров
        st.header("📊 Общая статистика")

        total_stats_result = conn.query('SELECT SUM(count), SUM(total_amount) FROM cars', ttl=0)

        if not total_stats_result.empty and not pd.isna(total_stats_result.iloc[0, 0]):
            total_cars = int(total_stats_result.iloc[0, 0])
            total_amount = int(total_stats_result.iloc[0, 1])
            st.metric("Всего машин в системе", total_cars)
            st.metric("Общая сумма", f"{total_amount:,} тг")

            # Статистика по оплатам
            paid_cars_result = conn.query('SELECT SUM(count) FROM cars WHERE is_paid = TRUE', ttl=0)
            paid_cars = int(paid_cars_result.iloc[0, 0]) if not paid_cars_result.empty and not pd.isna(paid_cars_result.iloc[0, 0]) else 0

            paid_amount_result = conn.query('SELECT SUM(total_amount) FROM cars WHERE is_paid = TRUE', ttl=0)
            paid_amount = int(paid_amount_result.iloc[0, 0]) if not paid_amount_result.empty and not pd.isna(paid_amount_result.iloc[0, 0]) else 0

            st.divider()

            # СТАТУС ОПЛАТ ЗА СЕГОДНЯ (только для менеджеров)
            st.subheader("💰 Статус оплат")
            st.caption(f"📅 За сегодня ({date.today().strftime('%d.%m.%Y')})")

            # Получаем статистику за сегодня
            today_str = date.today().strftime('%Y-%m-%d')

            # Машины, оплаченные сегодня
            today_paid_result = conn.query('''
                SELECT SUM(count), SUM(total_amount)
                FROM cars
                WHERE payment_date = :today AND is_paid = TRUE
            ''', params={"today": today_str}, ttl=0)
            
            today_paid_cars = int(today_paid_result.iloc[0, 0]) if not today_paid_result.empty and not pd.isna(today_paid_result.iloc[0, 0]) else 0
            today_paid_amount = int(today_paid_result.iloc[0, 1]) if not today_paid_result.empty and not pd.isna(today_paid_result.iloc[0, 1]) else 0

            # Машины, добавленные сегодня но не оплаченные
            today_unpaid_result = conn.query('''
                SELECT SUM(count), SUM(total_amount)
                FROM cars
                WHERE date_added = :today AND is_paid = FALSE
            ''', params={"today": today_str}, ttl=0)
            
            today_unpaid_cars = int(today_unpaid_result.iloc[0, 0]) if not today_unpaid_result.empty and not pd.isna(today_unpaid_result.iloc[0, 0]) else 0
            today_unpaid_amount = int(today_unpaid_result.iloc[0, 1]) if not today_unpaid_result.empty and not pd.isna(today_unpaid_result.iloc[0, 1]) else 0

            # Всего машин за сегодня
            today_total_cars = today_paid_cars + today_unpaid_cars
            today_total_amount = today_paid_amount + today_unpaid_amount

            if today_total_cars > 0:
                col_today1, col_today2 = st.columns(2)

                with col_today1:
                    # Оплачено
                    st.markdown(f"""
                    <div style="background-color: #d4edda; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center;">
                            <span style="color: #28a745; font-size: 20px; margin-right: 8px;">✅</span>
                            <span style="color: #155724; font-weight: bold;">Оплачено</span>
                        </div>
                        <div style="font-size: 24px; font-weight: bold; color: #155724; margin: 5px 0;">
                            {today_paid_cars} машин
                        </div>
                        <div style="color: #6c757d; font-size: 14px;">
                            Сумма оплат<br>
                            <span style="font-size: 18px; font-weight: bold; color: #155724;">
                                {today_paid_amount:,} тг
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_today2:
                    # Не оплачено
                    st.markdown(f"""
                    <div style="background-color: #f8d7da; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center;">
                            <span style="color: #dc3545; font-size: 20px; margin-right: 8px;">❌</span>
                            <span style="color: #721c24; font-weight: bold;">Не оплачено</span>
                        </div>
                        <div style="font-size: 24px; font-weight: bold; color: #721c24; margin: 5px 0;">
                            {today_unpaid_cars} машин
                        </div>
                        <div style="color: #6c757d; font-size: 14px;">
                            К доплате<br>
                            <span style="font-size: 18px; font-weight: bold; color: #721c24;">
                                {today_unpaid_amount:,} тг
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Прогресс бар для сегодняшнего дня
                today_payment_percentage = (today_paid_cars / today_total_cars * 100) if today_total_cars > 0 else 0
                st.progress(today_payment_percentage / 100, text=f"Оплачено: {today_payment_percentage:.1f}%")

            else:
                st.info("📋 За сегодня машин не добавлялось")

        else:
            st.info("📈 Статистика появится после добавления машин")

# Футер с авторством
st.markdown("---")
st.markdown("""
<div style="
    text-align: center; 
    padding: 25px; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    border-radius: 15px; 
    margin: 30px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
">
    <p style="margin: 0; color: white; font-size: 16px;">
        💻 Сделал <strong>Алишер Бейсембеков</strong>, основатель и разработчик<br>
        <small style="opacity: 0.8;">© 2025 AutoTrade - Система управления автосалоном</small>
    </p>
</div>
""", unsafe_allow_html=True)

# Кнопка очистки данных (только для руководителя)
if is_leader(current_user):
    st.markdown("---")
    st.subheader("⚠️ Административные функции")

    # Обычная очистка данных
    if st.button("🗑️ Очистить все данные", type="secondary", help="Очистка с восстановлением автосалонов"):
        if st.button("Подтвердить очистку всех данных", type="primary"):
            engine = conn._instance
            with engine.connect() as connection:
                connection.execute(text('DELETE FROM cars'))
                connection.execute(text('DELETE FROM dealerships'))

                # Восстанавливаем базовые автосалоны
                for dealership in DEFAULT_DEALERSHIPS:
                    connection.execute(
                        text("INSERT INTO dealerships (name) VALUES (:name)"),
                        {"name": dealership}
                    )
                connection.commit()

            st.success("Все данные очищены!")
            st.rerun()

    st.markdown("---")

    # Полная очистка с паролем (ОПАСНО!)
    st.markdown("""
    <div style="background-color: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 15px; margin: 10px 0;">
        <h4 style="color: #d32f2f; margin-top: 0;">🚨 ОПАСНАЯ ЗОНА</h4>
        <p style="color: #d32f2f; margin: 0;">Полная очистка базы данных без восстановления</p>
    </div>
    """, unsafe_allow_html=True)

    destroy_password = st.text_input(
        "🔐 Пароль для полной очистки",
        type="password",
        placeholder="Введите пароль для подтверждения",
        help="Требуется специальный пароль для полной очистки"
    )

    if st.button("💥 ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ", type="primary", help="ВНИМАНИЕ: Полная очистка без восстановления!"):
        if destroy_password == "alisher_destroy":
            if st.button("🔥 ПОДТВЕРДИТЬ ПОЛНОЕ УНИЧТОЖЕНИЕ", type="primary"):
                engine = conn._instance
                with engine.connect() as connection:
                    connection.execute(text('DELETE FROM cars'))
                    connection.execute(text('DELETE FROM dealerships'))
                    connection.commit()

                st.success("💀 База данных полностью очищена!")
                st.warning("⚠️ Все автосалоны удалены! Потребуется ручное восстановление.")
                st.rerun()
        elif destroy_password:
            st.error("❌ Неверный пароль для полной очистки!")
        else:
            st.warning("⚠️ Введите пароль для подтверждения полной очистки")
