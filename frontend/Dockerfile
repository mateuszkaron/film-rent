# Używamy serwera Nginx do serwowania plików statycznych
FROM nginx:alpine

# Kopiujemy nasze pliki HTML do folderu serwera
COPY ./src /usr/share/nginx/html

# Kopiujemy naszą konfigurację Nginx (opcjonalne, ale zalecane dla React/Vue/SPA)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80