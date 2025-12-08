import pytest
from httpx import AsyncClient
from app.main import app
import random
import string

# Helper do losowych maili
def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

# --- WAŻNE: DEKORATOR ASYNCIO ---
@pytest.mark.asyncio
async def test_full_user_scenario_e2e():
    """
    SCENARIUSZ E2E (ASYNC):
    1. Rejestracja
    2. Logowanie
    3. Wypożyczenie
    4. Weryfikacja
    """
    
    # Używamy AsyncClient zamiast TestClient
    async with AsyncClient(app=app, base_url="http://test") as client:

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
        
        # Używamy słowa kluczowego AWAIT przy każdym zapytaniu
        response = await client.post("/register", json=register_payload)
        assert response.status_code == 200
        user_id = response.json()["_id"]

        # --- 2. LOGOWANIE ---
        # FastAPI oczekuje danych logowania jako FORM DATA, nie JSON!
        login_payload = {
            "username": email,
            "password": password
        }
        # W httpx używamy parametru 'data' dla formularzy
        response = await client.post("/login", data=login_payload)
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        auth_header = {"Authorization": f"Bearer {token}"}

        # --- 3. POBRANIE FILMÓW ---
        response = await client.get("/movies")
        assert response.status_code == 200
        movies = response.json()
        
        if len(movies) > 0:
            target_movie = movies[0]
            movie_id = target_movie["_id"]

            # --- 4. WYPOŻYCZENIE ---
            response = await client.post(f"/rentals?movie_id={movie_id}", headers=auth_header)
            
            # 200 = Sukces, 400 = Limit/Brak kopii (obie odpowiedzi są technicznie poprawne dla API)
            assert response.status_code in [200, 400] 

            if response.status_code == 200:
                # --- 5. WERYFIKACJA ---
                response = await client.get("/my-rentals", headers=auth_header)
                assert response.status_code == 200
                my_rentals = response.json()
                
                assert len(my_rentals) > 0
                # Sprawdzamy czy ID filmu się zgadza
                assert my_rentals[0]["movie_id"] == movie_id