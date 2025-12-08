# Używamy lekkiego obrazu Pythona
FROM python:3.9-slim

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy zależności i instalujemy je
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę kodu
COPY . .

RUN pytest

# Uruchamiamy serwer (host 0.0.0.0 jest ważny w Dockerze!)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]