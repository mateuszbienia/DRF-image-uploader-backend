# DRF-image-uploader-backend
Application made in DRF for recruitment purpose.

To run:

```
docker-compose build
docker-compose up
docker-compose exec app-backend python manage.py migrate
```

Migrate operation creates database with admin user with credencials:

- login: admin
- password: password

Migration will create also 3 account tiers Basic, Premium and Enterprise. App runs on http://127.0.0.1:8000

Task took me around 30 hours.