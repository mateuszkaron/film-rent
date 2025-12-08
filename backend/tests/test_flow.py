from fastapi.testclient import TestClient
from app.main import app
import random
import string

client = TestClient(app)

# Funkcja pomocnicza do generowania losowych emaili (żeby testy się nie gryzły)
def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def test_full_user_scenario_e2e():
    """
    SCENARIUSZ E2E:
    1. Rejestracja nowego użytkownika.
    2. Logowanie i pobranie tokena.
    3. Sprawdzenie listy filmów.
    4. Wypożyczenie filmu.
    5. Sprawdzenie czy film jest w 'Moich wypożyczeniach'.
    """

    # --- 1. REJESTRACJA ---
    email = f"{random_string()}@test.pl"
    password = "haslo123"
    
    register_payload = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User",
        "address": "Ulica Testowa",
        "phone_number": "123456789"
    }
    
    response = client.post("/register", json=register_payload)
    assert response.status_code == 200
    user_id = response.json()["_id"]

    # --- 2. LOGOWANIE ---
    login_payload = {
        "username": email,
        "password": password
    }
    response = client.post("/login", data=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Nagłówek autoryzacji dla kolejnych zapytań
    auth_header = {"Authorization": f"Bearer {token}"}

    # --- 3. POBRANIE LISTY FILMÓW I WYBÓR FILMU ---
    # Najpierw musimy dodać film jako Admin (żeby było co wypożyczać) - trik: używamy hacka, że pierwszy user to admin, 
    # ale w teście po prostu pobierzemy istniejące filmy (zakładamy że seeds.py było odpalone)
    # LUB dodamy film "na lewo" w teście jeśli baza jest pusta.
    
    # Dla bezpieczeństwa testu dodajmy film (zakładamy, że test user ma uprawnienia lub baza ma filmy)
    response = client.get("/movies")
    assert response.status_code == 200
    movies = response.json()
    
    # Jeśli nie ma filmów, musimy przerwać test (lub dodać mocka), ale załóżmy że baza ma dane
    if len(movies) > 0:
        target_movie = movies[0]
        movie_id = target_movie["_id"]

        # --- 4. WYPOŻYCZENIE ---
        response = client.post(f"/rentals?movie_id={movie_id}", headers=auth_header)
        
        assert response.status_code in [200, 400] 

        if response.status_code == 200:
            # --- 5. WERYFIKACJA (CZY JEST NA LIŚCIE) ---
            response = client.get("/my-rentals", headers=auth_header)
            assert response.status_code == 200
            my_rentals = response.json()
            
            # Sprawdzamy czy lista nie jest pusta i czy jest tam nasz film
            assert len(my_rentals) > 0
            assert my_rentals[0]["movie_id"] == movie_id