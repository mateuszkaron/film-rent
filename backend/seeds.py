import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime

# --- KONFIGURACJA ---
# Używamy adresu "mongo", bo skrypt uruchomimy wewnątrz sieci Dockera
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
DB_NAME = "wypozyczalnia_db"

# Konfiguracja haszowania haseł (taka sama jak w auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash(password):
    return pwd_context.hash(password)

# --- DANE: FILMY (Top 10 wg Filmweb/IMDb) ---
movies_data = [
    {
        "title": "Skazani na Shawshank",
        "genre": "Dramat",
        "director": "Frank Darabont",
        "duration_minutes": 142,
        "rating": 8.8,
        "description": "Adaptacja opowiadania Stephena Kinga. Niesłusznie skazany bankier Andy Dufresne stara się przetrwać w brutalnym świecie więzienia Shawshank.",
        "actors": ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
        "total_copies": 5,
        "available_copies": 5
    },
    {
        "title": "Nietykalni",
        "genre": "Biograficzny",
        "director": "Olivier Nakache",
        "duration_minutes": 112,
        "rating": 8.6,
        "description": "Sparaliżowany milioner zatrudnia do opieki młodego chłopaka z przedmieścia, który właśnie wyszedł z więzienia. Zderzenie dwóch różnych światów.",
        "actors": ["François Cluzet", "Omar Sy", "Anne Le Ny"],
        "total_copies": 3,
        "available_copies": 3
    },
    {
        "title": "Ojciec chrzestny",
        "genre": "Dramat, Gangsterski",
        "director": "Francis Ford Coppola",
        "duration_minutes": 175,
        "rating": 8.7,
        "description": "Opowieść o nowojorskiej rodzinie mafijnej. Starzejący się Don Corleone pragnie przekazać władzę swojemu synowi.",
        "actors": ["Marlon Brando", "Al Pacino", "James Caan"],
        "total_copies": 4,
        "available_copies": 4
    },
    {
        "title": "Dwunastu gniewnych ludzi",
        "genre": "Dramat sądowy",
        "director": "Sidney Lumet",
        "duration_minutes": 96,
        "rating": 8.7,
        "description": "Dwunastu przysięgłych ma wydać wyrok w procesie o morderstwo. Jeden z nich ma wątpliwości co do winy oskarżonego.",
        "actors": ["Henry Fonda", "Lee J. Cobb", "Martin Balsam"],
        "total_copies": 2,
        "available_copies": 2
    },
    {
        "title": "Pulp Fiction",
        "genre": "Gangsterski",
        "director": "Quentin Tarantino",
        "duration_minutes": 154,
        "rating": 8.3,
        "description": "Przemoc i odkupienie w opowieści o dwóch płatnych mordercach, żonie gangstera i bokserze.",
        "actors": ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
        "total_copies": 6,
        "available_copies": 6
    },
    {
        "title": "Władca Pierścieni: Powrót króla",
        "genre": "Fantasy",
        "director": "Peter Jackson",
        "duration_minutes": 201,
        "rating": 8.4,
        "description": "Zwieńczenie trylogii. Frodo i Sam zbliżają się do Góry Przeznaczenia, by zniszczyć Jedyny Pierścień.",
        "actors": ["Elijah Wood", "Viggo Mortensen", "Ian McKellen"],
        "total_copies": 10,
        "available_copies": 10
    },
    {
        "title": "Forrest Gump",
        "genre": "Dramat, Komedia",
        "director": "Robert Zemeckis",
        "duration_minutes": 142,
        "rating": 8.5,
        "description": "Historia życia Forresta Gumpa, człowieka o niskim ilorazie inteligencji, który staje się świadkiem ważnych wydarzeń historycznych.",
        "actors": ["Tom Hanks", "Robin Wright", "Gary Sinise"],
        "total_copies": 5,
        "available_copies": 5
    },
    {
        "title": "Incepcja",
        "genre": "Sci-Fi",
        "director": "Christopher Nolan",
        "duration_minutes": 148,
        "rating": 8.3,
        "description": "Czasy, gdy technologia pozwala na wchodzenie w czyjeś sny. Złodziej Cobb otrzymuje zadanie zaszczepienia idei w umyśle ofiary.",
        "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
        "total_copies": 4,
        "available_copies": 4
    },
    {
        "title": "Matrix",
        "genre": "Sci-Fi",
        "director": "Lana Wachowski",
        "duration_minutes": 136,
        "rating": 7.6,
        "description": "Haker Neo dowiaduje się od tajemniczych rebeliantów, że świat, w którym żyje, jest tylko obrazem przesyłanym do jego mózgu.",
        "actors": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
        "total_copies": 7,
        "available_copies": 7
    },
    {
        "title": "Joker",
        "genre": "Dramat, Psychologiczny",
        "director": "Todd Phillips",
        "duration_minutes": 122,
        "rating": 8.4,
        "description": "Historia jednego z najsłynniejszych superprzestępców uniwersum DC. Arthur Fleck, lekceważony przez społeczeństwo, popada w szaleństwo.",
        "actors": ["Joaquin Phoenix", "Robert De Niro", "Zazie Beetz"],
        "total_copies": 8,
        "available_copies": 8
    }
]

# --- DANE: UŻYTKOWNICY (1 Admin + 4 Klientów) ---
users_data = [
    {
        "first_name": "Admin",
        "last_name": "Systemu",
        "email": "admin@op.pl",
        "password": "admin",  # Hasło 'admin'
        "role": "admin",
        "address": "Serwerownia 1, 00-001 Warszawa",
        "phone_number": "999-999-999"
    },
    {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "jan@kowalski.pl",
        "password": "user123", # Hasło 'user123'
        "role": "user",
        "address": "ul. Długa 15, 30-002 Kraków",
        "phone_number": "501-100-100"
    },
    {
        "first_name": "Anna",
        "last_name": "Nowak",
        "email": "anna@nowak.pl",
        "password": "user123",
        "role": "user",
        "address": "ul. Kwiatowa 7, 80-003 Gdańsk",
        "phone_number": "602-200-200"
    },
    {
        "first_name": "Piotr",
        "last_name": "Wiśniewski",
        "email": "piotr@wisniewski.pl",
        "password": "user123",
        "role": "user",
        "address": "ul. Marszałkowska 50, 00-100 Warszawa",
        "phone_number": "703-300-300"
    },
    {
        "first_name": "Katarzyna",
        "last_name": "Wójcik",
        "email": "kasia@wojcik.pl",
        "password": "user123",
        "role": "user",
        "address": "ul. Słoneczna 4, 50-004 Wrocław",
        "phone_number": "804-400-400"
    }
]

async def seed_db():
    print(f"🔄 Łączenie z bazą: {MONGO_URL} ...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # 1. Czyszczenie bazy (Reset)
    print("🗑️  Usuwanie starych danych...")
    await db.movies.drop()
    await db.users.drop()
    await db.rentals.drop()
    
    # 2. Dodawanie Filmów
    print(f"🎬 Dodawanie {len(movies_data)} filmów...")
    for movie in movies_data:
        movie["added_at"] = datetime.utcnow()
        await db.movies.insert_one(movie)
        
    # 3. Dodawanie Użytkowników
    print(f"👤 Dodawanie {len(users_data)} użytkowników...")
    for user in users_data:
        # Haszowanie hasła
        user_db = user.copy()
        user_db["hashed_password"] = get_hash(user.pop("password"))
        user_db["registered_at"] = datetime.utcnow()
        user_db["active_rentals"] = []
        
        await db.users.insert_one(user_db)

    print("✅ Baza danych została pomyślnie zasilona!")
    print("\n--- DANE DO LOGOWANIA ---")
    print("ADMIN: admin@op.pl / admin")
    print("USER:  jan@kowalski.pl / user123")
    client.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_db())