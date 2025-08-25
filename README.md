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

## Ads API Example

```bash
curl -X POST http://localhost:8000/api/ads/ \
  -H "Authorization: Bearer <JWT>" \
  -F "title=Spacious 2-Bedroom Apartment" \
  -F "description=..." \
  -F "monthly_rent=4500000" \
  -F "property_type=APARTMENT" \
  -F "bedrooms=2" -F "bathrooms=1" -F "area_m2=65" \
  -F "address=Yakkasaroy, Tashkent" \
  -F "latitude=41.3111" -F "longitude=69.2797" \
  -F "amenities=1" -F "amenities=3" \
  -F "contact_name=Ali" \
  -F "contact_phone=+998901234567" \
  -F "images=@/path/img1.jpg" -F "images=@/path/img2.jpg"
```

### Integration notes

Submit the form as `multipart/form-data` using the following field names:

* `title`
* `description`
* `monthly_rent`
* `property_type`
* `bedrooms`
* `bathrooms`
* `area_m2`
* `address`
* `latitude` (required)
* `longitude` (required)
* `amenities` (repeatable)
* `contact_name`
* `contact_phone`
* `images` (repeatable)

Prices are integer UZS values. Successful creation returns the new ad with status
`PENDING` until moderated. Latitude and longitude must be included.
