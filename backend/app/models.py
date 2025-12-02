from pydantic import BaseModel, Field, BeforeValidator, ConfigDict, EmailStr
from typing import List, Optional, Annotated
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

# --- MODEL FILMU (Poprawka: dodano actors, added_at) ---
class MovieModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    genre: str
    director: str
    duration_minutes: int
    rating: float
    description: str
    actors: List[str] = []       # <--- NOWE
    added_at: datetime = Field(default_factory=datetime.utcnow) # <--- NOWE
    total_copies: int = 1
    available_copies: int = 1
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

# --- MODEL REJESTRACJI (Poprawka: dodano adres, telefon) ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    address: str                 # <--- NOWE
    phone_number: str            # <--- NOWE

# --- MODEL EDYCJI UŻYTKOWNIKA ---
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None

# --- MODEL UŻYTKOWNIKA W BAZIE ---
class UserModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    hashed_password: str
    first_name: Optional[str] = None    # <--- ZMIANA: opcjonalne dla kompatybilności z istniejącymi użytkownikami
    last_name: Optional[str] = None     # <--- ZMIANA: opcjonalne dla kompatybilności z istniejącymi użytkownikami
    address: Optional[str] = None       # <--- NOWE
    phone_number: Optional[str] = None  # <--- NOWE
    registered_at: Optional[datetime] = Field(default_factory=datetime.utcnow) # <--- ZMIANA: opcjonalne
    role: str = "user"
    active_rentals: List[str] = []

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

# --- MODEL WYPOŻYCZENIA ---
class RentalModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    movie_id: str
    movie_title: Optional[str] = "Film"
    user_fullname: Optional[str] = "Klient" # <--- NOWE (Dane klienta na liście)
    user_email: Optional[str] = ""
    rented_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)