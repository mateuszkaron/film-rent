from fastapi import FastAPI, HTTPException, Depends, status, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from app.models import MovieModel, UserModel, RentalModel, UserCreate, UserUpdate
from app.auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
import os

app = FastAPI(title="Wypożyczalnia Video - Final Version")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-service-989611935636.europe-central2.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(status_code=200)

# --- BAZA DANYCH ---
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "wypozyczalnia_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# --- SECURITY ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Brak autoryzacji",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.users.find_one({"email": email})
    if user is None: raise credentials_exception
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Wymagane uprawnienia Administratora")
    return current_user

# ==========================================
# AUTH (Rejestracja / Logowanie)
# ==========================================

@app.post("/register", response_model=UserModel)
async def register(user: UserCreate):
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email zajęty")
    
    user_data = {
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "address": user.address,
        "phone_number": user.phone_number,
        "registered_at": datetime.utcnow(),
        "role": "user",
        "active_rentals": []
    }

    if await db.users.count_documents({}) == 0:
        user_data["role"] = "admin"
    
    new_user = await db.users.insert_one(user_data)
    return await db.users.find_one({"_id": new_user.inserted_id})

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Błędne dane")
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(user["_id"]), "role": user["role"]}

# ==========================================
# FILMY
# ==========================================

@app.get("/movies", response_model=List[MovieModel])
async def get_movies(search: Optional[str] = None, sort_by: Optional[str] = "title"):
    query = {}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"genre": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.movies.find(query)
    if sort_by == "rating":
        cursor.sort("rating", -1)
    else:
        cursor.sort("title", 1)

    return await cursor.to_list(100)

@app.post("/movies", response_model=MovieModel)
async def add_movie(movie: MovieModel, _: dict = Depends(get_admin_user)):
    new_movie = await db.movies.insert_one(movie.model_dump(by_alias=True, exclude=["id"]))
    return await db.movies.find_one({"_id": new_movie.inserted_id})

@app.put("/movies/{movie_id}")
async def update_movie(movie_id: str, movie_update: dict, _: dict = Depends(get_admin_user)):
    movie_update.pop("_id", None) 
    result = await db.movies.update_one(
        {"_id": ObjectId(movie_id)}, 
        {"$set": movie_update}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Film nie istnieje")
    return {"message": "Zaktualizowano"}

@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: str, _: dict = Depends(get_admin_user)):
    if await db.rentals.find_one({"movie_id": movie_id, "returned_at": None}):
        raise HTTPException(status_code=400, detail="Nie można usunąć wypożyczonego filmu!")

    await db.movies.delete_one({"_id": ObjectId(movie_id)})
    return {"message": "Film usunięty"}

# ==========================================
# KLIENCI
# ==========================================

@app.get("/users", response_model=List[UserModel])
async def get_users(_: dict = Depends(get_admin_user)):
    try:
        return await db.users.find().to_list(100)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")

@app.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, _: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    
    # Aktualizujemy tylko pola przesłane (niepuste)
    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": update_data}
        )
    return {"message": "Użytkownik zaktualizowany"}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, _: dict = Depends(get_admin_user)):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    
    if len(user.get("active_rentals", [])) > 0:
         raise HTTPException(status_code=400, detail="Klient ma nieoddane filmy.")
    
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "Klient usunięty"}

# ==========================================
# WYPOŻYCZENIA
# ==========================================

@app.post("/rentals")
async def rent_movie(movie_id: str, user_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    target_user_id = user_id if (current_user["role"] == "admin" and user_id) else str(current_user["_id"])
    
    target_user = await db.users.find_one({"_id": ObjectId(target_user_id)})
    if not target_user: raise HTTPException(404, "Użytkownik nie istnieje")

    if len(target_user.get("active_rentals", [])) >= 3:
        raise HTTPException(400, "Limit 3 filmów osiągnięty!")

    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie or movie["available_copies"] <= 0:
        raise HTTPException(400, "Brak dostępnych kopii")

    rental_data = {
        "user_id": target_user_id,
        "movie_id": movie_id,
        "movie_title": movie["title"],
        "user_fullname": f"{target_user.get('first_name','')} {target_user.get('last_name','')}", 
        "user_email": target_user["email"],
        "rented_at": datetime.utcnow(),
        "due_date": datetime.utcnow() + timedelta(days=2),
        "returned_at": None
    }
    new_rental = await db.rentals.insert_one(rental_data)
    
    await db.movies.update_one({"_id": movie["_id"]}, {"$inc": {"available_copies": -1}})
    await db.users.update_one({"_id": target_user["_id"]}, {"$push": {"active_rentals": str(new_rental.inserted_id)}})

    return {"message": "Wypożyczono", "due_date": rental_data["due_date"]}

@app.get("/admin/rentals", response_model=List[RentalModel])
async def get_all_rentals(_: dict = Depends(get_admin_user)):
    return await db.rentals.find().sort("rented_at", -1).to_list(200)

@app.post("/rentals/return/{rental_id}")
async def return_movie(rental_id: str, _: dict = Depends(get_admin_user)):
    rental = await db.rentals.find_one({"_id": ObjectId(rental_id)})
    if not rental or rental["returned_at"]:
        raise HTTPException(400, "Wypożyczenie nieaktywne lub nie istnieje")
        
    await db.rentals.update_one(
        {"_id": ObjectId(rental_id)},
        {"$set": {"returned_at": datetime.utcnow()}}
    )
    
    await db.movies.update_one({"_id": ObjectId(rental["movie_id"])}, {"$inc": {"available_copies": 1}})
    await db.users.update_one(
        {"_id": ObjectId(rental["user_id"])},
        {"$pull": {"active_rentals": str(rental_id)}}
    )
    return {"message": "Zwrot przyjęty"}

@app.get("/my-rentals", response_model=List[RentalModel])
async def get_my_rentals(current_user: dict = Depends(get_current_user)):
    return await db.rentals.find({"user_id": str(current_user["_id"])}).sort("rented_at", -1).to_list(50)