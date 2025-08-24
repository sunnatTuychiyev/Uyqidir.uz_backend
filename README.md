# Uyqidir Authentication API

Django REST API providing authentication for **uyqidir.uz**.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Example requests

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"John Doe","email":"john@example.com","phone_number":"+998901112233","password":"StrongPass123","password_confirm":"StrongPass123","accept_terms":true}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"john@example.com","password":"StrongPass123"}'

# Refresh token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<refresh>"}'

# Current user
curl http://localhost:8000/api/auth/me/ \
  -H 'Authorization: Bearer <access>'

# Logout
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<refresh>"}'
```
