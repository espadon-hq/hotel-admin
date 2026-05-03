"""
models.py — Pydantic-схеми для валідації даних.
Кожна таблиця має 3 схеми:
  - Base   — спільні поля
  - Create — для POST (без ID)
  - Out    — для відповіді (з ID та joined полями)
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


# ─── UserRole ─────────────────────────────────────────────────────────────────
class UserRoleBase(BaseModel):
    Title: str
    Description: Optional[str] = None

class UserRoleCreate(UserRoleBase):
    pass

class UserRoleOut(UserRoleBase):
    ID_Role: int
    class Config:
        from_attributes = True


# ─── User ─────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    Full_name: str
    Login: str
    Email: Optional[str] = None
    Phone: Optional[str] = None
    ID_Role: Optional[int] = None
    Interface_language: Optional[str] = "uk"

class UserCreate(UserBase):
    Password_hash: str

class UserOut(UserBase):
    ID_User: int
    Created_at: Optional[datetime] = None
    role_title: Optional[str] = None
    bookings_count: Optional[int] = None
    class Config:
        from_attributes = True


# ─── Hotel ────────────────────────────────────────────────────────────────────
class HotelBase(BaseModel):
    Name: str
    Description: Optional[str] = None
    Address: Optional[str] = None
    City: Optional[str] = None
    Stars: Optional[int] = None
    Phone: Optional[str] = None
    Email: Optional[str] = None
    Coordinates: Optional[str] = None
    Check_in_time: Optional[time] = None
    Check_out_time: Optional[time] = None

class HotelCreate(HotelBase):
    pass

class HotelOut(HotelBase):
    ID_Hotel: int
    rooms_count: Optional[int] = None
    reviews_count: Optional[int] = None
    avg_rating: Optional[float] = None
    class Config:
        from_attributes = True


# ─── RoomType ─────────────────────────────────────────────────────────────────
class RoomTypeBase(BaseModel):
    Title: str
    Description: Optional[str] = None
    Max_adults: Optional[int] = None
    Max_children: Optional[int] = None
    Area: Optional[float] = None
    Beds_count: Optional[int] = None

class RoomTypeCreate(RoomTypeBase):
    pass

class RoomTypeOut(RoomTypeBase):
    ID_RoomType: int
    class Config:
        from_attributes = True


# ─── RoomStatus ───────────────────────────────────────────────────────────────
class RoomStatusBase(BaseModel):
    Title: str
    Description: Optional[str] = None

class RoomStatusOut(RoomStatusBase):
    ID_RoomStatus: int
    class Config:
        from_attributes = True


# ─── Room ─────────────────────────────────────────────────────────────────────
class RoomBase(BaseModel):
    Room_number: Optional[str] = None
    Floor: Optional[int] = None
    ID_Hotel: Optional[int] = None
    ID_RoomType: Optional[int] = None
    ID_RoomStatus: Optional[int] = None
    Price_per_day: Optional[Decimal] = None

class RoomCreate(RoomBase):
    pass

class RoomOut(RoomBase):
    ID_Room: int
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    type_title: Optional[str] = None
    status_title: Optional[str] = None
    Max_adults: Optional[int] = None
    Area: Optional[float] = None
    class Config:
        from_attributes = True


# ─── BookingStatus ────────────────────────────────────────────────────────────
class BookingStatusOut(BaseModel):
    ID_BookingStatus: int
    Title: str
    Description: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Booking ──────────────────────────────────────────────────────────────────
class BookingBase(BaseModel):
    ID_User: Optional[int] = None
    ID_Room: Optional[int] = None
    Check_in_date: Optional[date] = None
    Check_out_date: Optional[date] = None
    ID_BookingStatus: Optional[int] = None
    Total_amount: Optional[Decimal] = None

class BookingCreate(BookingBase):
    pass

class BookingOut(BookingBase):
    ID_Booking: int
    user_name: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    Room_number: Optional[str] = None
    status_title: Optional[str] = None
    room_type: Optional[str] = None
    class Config:
        from_attributes = True


# ─── PaymentMethod ────────────────────────────────────────────────────────────
class PaymentMethodOut(BaseModel):
    ID_PaymentMethod: int
    Title: str
    Description: Optional[str] = None
    Commission: Optional[Decimal] = None
    Currency: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Payment ──────────────────────────────────────────────────────────────────
class PaymentBase(BaseModel):
    ID_Booking: Optional[int] = None
    Amount: Optional[Decimal] = None
    Status: Optional[str] = None
    ID_PaymentMethod: Optional[int] = None
    Transaction_ID: Optional[str] = None
    Payment_date: Optional[datetime] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase):
    ID_Payment: int
    method_title: Optional[str] = None
    user_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── ExtraService ─────────────────────────────────────────────────────────────
class ExtraServiceBase(BaseModel):
    ID_Hotel: Optional[int] = None
    Title: Optional[str] = None
    Description: Optional[str] = None
    Price: Optional[Decimal] = None

class ExtraServiceCreate(ExtraServiceBase):
    pass

class ExtraServiceOut(ExtraServiceBase):
    ID_Service: int
    hotel_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Review ───────────────────────────────────────────────────────────────────
class ReviewBase(BaseModel):
    ID_User: Optional[int] = None
    ID_Hotel: Optional[int] = None
    Rating: Optional[int] = None
    Comment: Optional[str] = None
    Photo_URL: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    ID_Review: int
    Created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    hotel_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Статистика для дашборду ──────────────────────────────────────────────────
class StatsOut(BaseModel):
    hotels: int
    rooms: int
    bookings: int
    users: int
    revenue: float
    status_counts: list
    hotel_stats: list