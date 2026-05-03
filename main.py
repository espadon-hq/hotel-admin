"""
main.py — головний файл FastAPI-додатку.
Запуск: uvicorn main:app --reload
Документація API: http://localhost:8000/docs
"""

from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    BookingCreate,
    HotelCreate,
    RoomCreate,
    UserCreate,
)

app = FastAPI(
    title="Hotel Booking Admin",
    description="REST API для управління готельною системою бронювань",
    version="1.0.0",
)

# Роздача статичних файлів (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/index.html")


# ═══════════════════════════════════════════════════════════════════════════════
# СТАТИСТИКА — Дашборд
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/stats", tags=["Dashboard"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Загальна статистика для головної сторінки."""
    counts = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM public."Hotel")   AS hotels,
            (SELECT COUNT(*) FROM public."Room")    AS rooms,
            (SELECT COUNT(*) FROM public."Booking") AS bookings,
            (SELECT COUNT(*) FROM public."User")    AS users,
            (SELECT COALESCE(SUM("Total_amount"),0) FROM public."Booking") AS revenue
    """))
    row = counts.fetchone()

    status_counts = await db.execute(text("""
        SELECT bs."Title", COUNT(b."ID_Booking") AS count
        FROM public."BookingStatus" bs
        LEFT JOIN public."Booking" b ON b."ID_BookingStatus" = bs."ID_BookingStatus"
        GROUP BY bs."Title", bs."ID_BookingStatus"
        ORDER BY bs."ID_BookingStatus"
    """))

    hotel_stats = await db.execute(text("""
        SELECT h."Name",
               COUNT(b."ID_Booking") AS bookings,
               COALESCE(SUM(b."Total_amount"), 0) AS revenue
        FROM public."Hotel" h
        LEFT JOIN public."Room" r ON r."ID_Hotel" = h."ID_Hotel"
        LEFT JOIN public."Booking" b ON b."ID_Room" = r."ID_Room"
        GROUP BY h."ID_Hotel", h."Name"
        ORDER BY revenue DESC
    """))

    return {
        "hotels":        row.hotels,
        "rooms":         row.rooms,
        "bookings":      row.bookings,
        "users":         row.users,
        "revenue":       float(row.revenue),
        "status_counts": [dict(r._mapping) for r in status_counts.fetchall()],
        "hotel_stats":   [dict(r._mapping) for r in hotel_stats.fetchall()],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ГОТЕЛІ
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/hotels", tags=["Hotels"])
async def get_hotels(
    search: Optional[str] = Query(None, description="Пошук по назві, місту, адресі"),
    city:   Optional[str] = Query(None, description="Фільтр по місту"),
    stars:  Optional[int] = Query(None, description="Фільтр по зірках"),
    sort:   str = Query("ID_Hotel", description="Поле сортування"),
    order:  str = Query("ASC", description="ASC або DESC"),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"ID_Hotel", "Name", "City", "Stars"}
    sort_field = f'h."{sort}"' if sort in allowed else 'h."ID_Hotel"'
    sort_order = "DESC" if order.upper() == "DESC" else "ASC"

    conditions, params = [], {}
    if search:
        conditions.append('(h."Name" ILIKE :search OR h."City" ILIKE :search OR h."Address" ILIKE :search)')
        params["search"] = f"%{search}%"
    if city:
        conditions.append('h."City" = :city')
        params["city"] = city
    if stars:
        conditions.append('h."Stars" = :stars')
        params["stars"] = stars

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(text(f"""
        SELECT h.*,
               COUNT(DISTINCT r."ID_Room")    AS rooms_count,
               COUNT(DISTINCT rv."ID_Review") AS reviews_count,
               ROUND(AVG(rv."Rating")::numeric, 1) AS avg_rating
        FROM public."Hotel" h
        LEFT JOIN public."Room"   r  ON r."ID_Hotel"  = h."ID_Hotel"
        LEFT JOIN public."Review" rv ON rv."ID_Hotel" = h."ID_Hotel"
        {where}
        GROUP BY h."ID_Hotel"
        ORDER BY {sort_field} {sort_order}
    """), params)
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/hotels/{hotel_id}", tags=["Hotels"])
async def get_hotel(hotel_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('SELECT * FROM public."Hotel" WHERE "ID_Hotel" = :id'),
        {"id": hotel_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Готель не знайдено")
    return dict(row._mapping)


@app.post("/api/hotels", tags=["Hotels"], status_code=201)
async def create_hotel(hotel: HotelCreate, db: AsyncSession = Depends(get_db)):
    data = hotel.model_dump(exclude_none=True)
    cols = ", ".join(f'"{k}"' for k in data)
    vals = ", ".join(f":{k}" for k in data)
    result = await db.execute(
        text(f'INSERT INTO public."Hotel" ({cols}) VALUES ({vals}) RETURNING *'),
        data
    )
    return dict(result.fetchone()._mapping)


@app.put("/api/hotels/{hotel_id}", tags=["Hotels"])
async def update_hotel(hotel_id: int, hotel: HotelCreate, db: AsyncSession = Depends(get_db)):
    data = hotel.model_dump(exclude_none=True)
    sets = ", ".join(f'"{k}" = :{k}' for k in data)
    data["id"] = hotel_id
    result = await db.execute(
        text(f'UPDATE public."Hotel" SET {sets} WHERE "ID_Hotel" = :id RETURNING *'),
        data
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Готель не знайдено")
    return dict(row._mapping)


@app.delete("/api/hotels/{hotel_id}", tags=["Hotels"])
async def delete_hotel(hotel_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('DELETE FROM public."Hotel" WHERE "ID_Hotel" = :id RETURNING "ID_Hotel"'),
        {"id": hotel_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Готель не знайдено")
    return {"message": "Готель видалено"}


# ═══════════════════════════════════════════════════════════════════════════════
# НОМЕРИ
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/rooms", tags=["Rooms"])
async def get_rooms(
    search: Optional[str] = None,
    hotel:  Optional[int] = None,
    status: Optional[int] = None,
    sort:   str = Query("ID_Room"),
    order:  str = Query("ASC"),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"ID_Room", "Room_number", "Floor", "Price_per_day"}
    sort_field = f'r."{sort}"' if sort in allowed else 'r."ID_Room"'
    sort_order = "DESC" if order.upper() == "DESC" else "ASC"

    conditions, params = [], {}
    if search:
        conditions.append('(r."Room_number" ILIKE :search OR h."Name" ILIKE :search)')
        params["search"] = f"%{search}%"
    if hotel:
        conditions.append('r."ID_Hotel" = :hotel')
        params["hotel"] = hotel
    if status:
        conditions.append('r."ID_RoomStatus" = :status')
        params["status"] = status

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(text(f"""
        SELECT r.*,
               h."Name" AS hotel_name, h."City" AS hotel_city,
               rt."Title" AS type_title, rt."Max_adults", rt."Area",
               rs."Title" AS status_title
        FROM public."Room" r
        LEFT JOIN public."Hotel"      h  ON h."ID_Hotel"      = r."ID_Hotel"
        LEFT JOIN public."RoomType"   rt ON rt."ID_RoomType"  = r."ID_RoomType"
        LEFT JOIN public."RoomStatus" rs ON rs."ID_RoomStatus"= r."ID_RoomStatus"
        {where}
        ORDER BY {sort_field} {sort_order}
    """), params)
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/rooms/{room_id}", tags=["Rooms"])
async def get_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('SELECT * FROM public."Room" WHERE "ID_Room" = :id'),
        {"id": room_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Номер не знайдено")
    return dict(row._mapping)


@app.post("/api/rooms", tags=["Rooms"], status_code=201)
async def create_room(room: RoomCreate, db: AsyncSession = Depends(get_db)):
    data = room.model_dump(exclude_none=True)
    cols = ", ".join(f'"{k}"' for k in data)
    vals = ", ".join(f":{k}" for k in data)
    result = await db.execute(
        text(f'INSERT INTO public."Room" ({cols}) VALUES ({vals}) RETURNING *'),
        data
    )
    return dict(result.fetchone()._mapping)


@app.put("/api/rooms/{room_id}", tags=["Rooms"])
async def update_room(room_id: int, room: RoomCreate, db: AsyncSession = Depends(get_db)):
    data = room.model_dump(exclude_none=True)
    sets = ", ".join(f'"{k}" = :{k}' for k in data)
    data["id"] = room_id
    result = await db.execute(
        text(f'UPDATE public."Room" SET {sets} WHERE "ID_Room" = :id RETURNING *'),
        data
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Номер не знайдено")
    return dict(row._mapping)


@app.delete("/api/rooms/{room_id}", tags=["Rooms"])
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('DELETE FROM public."Room" WHERE "ID_Room" = :id RETURNING "ID_Room"'),
        {"id": room_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Номер не знайдено")
    return {"message": "Номер видалено"}


# ═══════════════════════════════════════════════════════════════════════════════
# БРОНЮВАННЯ
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/bookings", tags=["Bookings"])
async def get_bookings(
    search: Optional[str] = None,
    status: Optional[int] = None,
    sort:   str = Query("ID_Booking"),
    order:  str = Query("ASC"),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"ID_Booking", "Check_in_date", "Check_out_date", "Total_amount"}
    sort_field = f'b."{sort}"' if sort in allowed else 'b."ID_Booking"'
    sort_order = "DESC" if order.upper() == "DESC" else "ASC"

    conditions, params = [], {}
    if search:
        conditions.append('(u."Full_name" ILIKE :search OR h."Name" ILIKE :search)')
        params["search"] = f"%{search}%"
    if status:
        conditions.append('b."ID_BookingStatus" = :status')
        params["status"] = status

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(text(f"""
        SELECT b.*,
               u."Full_name"  AS user_name,
               h."Name"       AS hotel_name,
               h."City"       AS hotel_city,
               r."Room_number",
               bs."Title"     AS status_title,
               rt."Title"     AS room_type
        FROM public."Booking" b
        LEFT JOIN public."User"          u  ON u."ID_User"          = b."ID_User"
        LEFT JOIN public."Room"          r  ON r."ID_Room"          = b."ID_Room"
        LEFT JOIN public."Hotel"         h  ON h."ID_Hotel"         = r."ID_Hotel"
        LEFT JOIN public."BookingStatus" bs ON bs."ID_BookingStatus"= b."ID_BookingStatus"
        LEFT JOIN public."RoomType"      rt ON rt."ID_RoomType"     = r."ID_RoomType"
        {where}
        ORDER BY {sort_field} {sort_order}
    """), params)
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/bookings/{booking_id}", tags=["Bookings"])
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('SELECT * FROM public."Booking" WHERE "ID_Booking" = :id'),
        {"id": booking_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Бронювання не знайдено")
    return dict(row._mapping)


@app.post("/api/bookings", tags=["Bookings"], status_code=201)
async def create_booking(booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    data = booking.model_dump(exclude_none=True)
    cols = ", ".join(f'"{k}"' for k in data)
    vals = ", ".join(f":{k}" for k in data)
    result = await db.execute(
        text(f'INSERT INTO public."Booking" ({cols}) VALUES ({vals}) RETURNING *'),
        data
    )
    return dict(result.fetchone()._mapping)


@app.put("/api/bookings/{booking_id}", tags=["Bookings"])
async def update_booking(booking_id: int, booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    data = booking.model_dump(exclude_none=True)
    sets = ", ".join(f'"{k}" = :{k}' for k in data)
    data["id"] = booking_id
    result = await db.execute(
        text(f'UPDATE public."Booking" SET {sets} WHERE "ID_Booking" = :id RETURNING *'),
        data
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Бронювання не знайдено")
    return dict(row._mapping)


@app.delete("/api/bookings/{booking_id}", tags=["Bookings"])
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('DELETE FROM public."Booking" WHERE "ID_Booking" = :id RETURNING "ID_Booking"'),
        {"id": booking_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Бронювання не знайдено")
    return {"message": "Бронювання видалено"}


# ═══════════════════════════════════════════════════════════════════════════════
# КОРИСТУВАЧІ
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/users", tags=["Users"])
async def get_users(
    search: Optional[str] = None,
    role:   Optional[int] = None,
    sort:   str = Query("ID_User"),
    order:  str = Query("ASC"),
    db: AsyncSession = Depends(get_db),
):
    conditions, params = [], {}
    if search:
        conditions.append('(u."Full_name" ILIKE :search OR u."Email" ILIKE :search OR u."Login" ILIKE :search)')
        params["search"] = f"%{search}%"
    if role:
        conditions.append('u."ID_Role" = :role')
        params["role"] = role

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(text(f"""
        SELECT u."ID_User", u."Full_name", u."Login", u."Email", u."Phone",
               u."Created_at", u."Interface_language", u."ID_Role",
               ur."Title" AS role_title,
               COUNT(b."ID_Booking") AS bookings_count
        FROM public."User" u
        LEFT JOIN public."UserRole" ur ON ur."ID_Role"  = u."ID_Role"
        LEFT JOIN public."Booking"  b  ON b."ID_User"   = u."ID_User"
        {where}
        GROUP BY u."ID_User", ur."Title"
        ORDER BY u."ID_User" ASC
    """), params)
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/users/{user_id}", tags=["Users"])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('SELECT * FROM public."User" WHERE "ID_User" = :id'),
        {"id": user_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return dict(row._mapping)


@app.post("/api/users", tags=["Users"], status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    data = user.model_dump(exclude_none=True)
    cols = ", ".join(f'"{k}"' for k in data)
    vals = ", ".join(f":{k}" for k in data)
    result = await db.execute(
        text(f'INSERT INTO public."User" ({cols}) VALUES ({vals}) RETURNING *'),
        data
    )
    return dict(result.fetchone()._mapping)


@app.put("/api/users/{user_id}", tags=["Users"])
async def update_user(user_id: int, user: UserCreate, db: AsyncSession = Depends(get_db)):
    data = user.model_dump(exclude_none=True)
    sets = ", ".join(f'"{k}" = :{k}' for k in data)
    data["id"] = user_id
    result = await db.execute(
        text(f'UPDATE public."User" SET {sets} WHERE "ID_User" = :id RETURNING *'),
        data
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return dict(row._mapping)


@app.delete("/api/users/{user_id}", tags=["Users"])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text('DELETE FROM public."User" WHERE "ID_User" = :id RETURNING "ID_User"'),
        {"id": user_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    return {"message": "Користувача видалено"}


# ═══════════════════════════════════════════════════════════════════════════════
# ДОВІДНИКИ (тільки читання)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/booking-statuses", tags=["References"])
async def get_booking_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT * FROM public."BookingStatus" ORDER BY "ID_BookingStatus"'))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/room-types", tags=["References"])
async def get_room_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT * FROM public."RoomType" ORDER BY "ID_RoomType"'))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/room-statuses", tags=["References"])
async def get_room_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT * FROM public."RoomStatus" ORDER BY "ID_RoomStatus"'))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/user-roles", tags=["References"])
async def get_user_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT * FROM public."UserRole" ORDER BY "ID_Role"'))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/payment-methods", tags=["References"])
async def get_payment_methods(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text('SELECT * FROM public."PaymentMethod" ORDER BY "ID_PaymentMethod"'))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/extra-services", tags=["References"])
async def get_extra_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT es.*, h."Name" AS hotel_name
        FROM public."ExtraService" es
        LEFT JOIN public."Hotel" h ON h."ID_Hotel" = es."ID_Hotel"
        ORDER BY es."ID_Service"
    """))
    return [dict(r._mapping) for r in result.fetchall()]


@app.get("/api/payments", tags=["Payments"])
async def get_payments(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    conditions, params = [], {}
    if search:
        conditions.append('(u."Full_name" ILIKE :search OR p."Transaction_ID" ILIKE :search)')
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    result = await db.execute(text(f"""
        SELECT p.*,
               pm."Title"     AS method_title,
               u."Full_name"  AS user_name
        FROM public."Payment" p
        LEFT JOIN public."PaymentMethod" pm ON pm."ID_PaymentMethod" = p."ID_PaymentMethod"
        LEFT JOIN public."Booking"       b  ON b."ID_Booking"        = p."ID_Booking"
        LEFT JOIN public."User"          u  ON u."ID_User"           = b."ID_User"
        {where}
        ORDER BY p."ID_Payment" ASC
    """), params)
    return [dict(r._mapping) for r in result.fetchall()]