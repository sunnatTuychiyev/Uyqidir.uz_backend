# Uyqidir.uz Backend

Django REST API providing authentication for Uyqidir.uz.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Example Requests

Register:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"John Doe","email":"john@example.com","phone_number":"+998901112233","password":"StrongP4ss","password_confirm":"StrongP4ss","accept_terms":true}'
```

Login:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"john@example.com","password":"StrongP4ss"}'
```

Current user:
```bash
curl http://localhost:8000/api/auth/me/ -H "Authorization: Bearer <access>"
```

Refresh token:
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<refresh>"}'
```

Logout:
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <access>" \
  -d '{"refresh":"<refresh>"}'
```

## Frontend Mapping

- **Sign Up** ➜ `POST /api/auth/register/`
  - full_name, email, phone_number, password, password_confirm, accept_terms
- **Login** ➜ `POST /api/auth/login/`
  - email, password

Error responses follow the format:
```json
{"errors": {"field": ["message"]}}
```
