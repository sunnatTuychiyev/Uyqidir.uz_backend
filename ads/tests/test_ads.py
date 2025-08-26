from __future__ import annotations

import base64
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ads.models import Ad, AdStatus, Amenity

User = get_user_model()

MIN_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def generate_image(name: str = "test.gif") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, MIN_GIF, content_type="image/gif")


class AdTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.user = User.objects.create_user(
            email="user@example.com", full_name="User", password="StrongPass123"
        )
        self.other = User.objects.create_user(
            email="other@example.com", full_name="Other", password="StrongPass123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com", full_name="Admin", password="AdminPass123"
        )
        self.amenity = Amenity.objects.create(name="Elevator", slug="elevator")
        self.list_url = reverse("ad-list")

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def create_ad(self, **kwargs):
        data = {
            "title": "Sample Ad",  # will override in tests for uniqueness
            "description": "Nice place",
            "monthly_rent": 1000,
            "property_type": "HOUSE",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_m2": 50,
            "address": "Main street",
            "latitude": 41.0,
            "longitude": 69.0,
            "amenities": [self.amenity.id],
            "images": [generate_image()],
        }
        data.update(kwargs)
        self.authenticate(self.user)
        return self.client.post(self.list_url, data, format="multipart")

    def test_create_ad_generates_slug_and_pending(self):
        resp = self.create_ad(title="House 1")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad = Ad.objects.get(id=resp.data["id"])
        self.assertEqual(ad.status, AdStatus.PENDING)
        self.assertTrue(ad.slug)

    def test_list_shows_own_pending_ads(self):
        resp = self.create_ad(title="Mine")
        ad_id = resp.data["id"]
        list_resp = self.client.get(self.list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in list_resp.data.get("results", [])]
        self.assertIn(ad_id, ids)

    def test_create_ad_with_base64_images(self):
        image_data = base64.b64encode(MIN_GIF).decode()
        payload = {
            "title": "Base64 House",
            "description": "Nice place",
            "monthly_rent": 1000,
            "property_type": "HOUSE",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_m2": 50,
            "address": "Main street",
            "latitude": 41.0,
            "longitude": 69.0,
            "amenities": [self.amenity.id],
            "images": [f"data:image/gif;base64,{image_data}"],
        }
        self.authenticate(self.user)
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad = Ad.objects.get(id=resp.data["id"])
        self.assertEqual(ad.images.count(), 1)

    def test_create_ad_with_unpadded_base64(self):
        image_data = base64.b64encode(MIN_GIF).decode().rstrip("=")
        payload = {
            "title": "Unpadded House",
            "description": "Nice place",
            "monthly_rent": 1000,
            "property_type": "HOUSE",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_m2": 50,
            "address": "Main street",
            "latitude": 41.0,
            "longitude": 69.0,
            "amenities": [self.amenity.id],
            "images": [f"data:image/gif;base64,{image_data}"],
        }
        self.authenticate(self.user)
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad = Ad.objects.get(id=resp.data["id"])
        self.assertEqual(ad.images.count(), 1)

    def test_frontend_payload(self):
        image_data = base64.b64encode(MIN_GIF).decode()
        a2 = Amenity.objects.create(name="Pool", slug="pool")
        a3 = Amenity.objects.create(name="Gym", slug="gym")
        payload = {
            "title": "Frontend",
            "description": "Nice place",
            "monthly_rent": 123456,
            "property_type": "APARTMENT",
            "bedrooms": 2,
            "bathrooms": 1,
            "area_m2": "65.0",
            "address": "Main street",
            "latitude": "41.31",
            "longitude": "69.28",
            "amenities": [self.amenity.id, a2.id, a3.id],
            "contact_name": "User",
            "contact_phone": "998901234567",
            "images": [f"data:image/gif;base64,{image_data}"],
        }
        self.authenticate(self.user)
        resp = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad = Ad.objects.get(id=resp.data["id"])
        self.assertEqual(str(ad.contact_phone), "+998901234567")
        self.assertEqual(ad.latitude, Decimal(payload["latitude"]))

    def test_create_ad_without_location(self):
        data = {
            "title": "No Location",
            "description": "Nice place",
            "monthly_rent": 1000,
            "property_type": "HOUSE",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_m2": 50,
            "address": "Main street",
            "amenities": [self.amenity.id],
            "images": [generate_image()],
        }
        self.authenticate(self.user)
        resp = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad = Ad.objects.get(id=resp.data["id"])
        self.assertIsNone(ad.latitude)
        self.assertIsNone(ad.longitude)

    def test_image_limit(self):
        images = [generate_image(f"{i}.gif") for i in range(10)]
        resp = self.create_ad(title="House 2", images=images)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ad_id = resp.data["id"]
        img11 = generate_image("11.gif")
        resp2 = self.client.post(
            reverse("ad-images", args=[ad_id]), {"image": img11}, format="multipart"
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permissions_and_updates(self):
        resp = self.create_ad(title="House 3")
        ad_id = resp.data["id"]
        # Non-owner cannot update
        self.authenticate(self.other)
        resp2 = self.client.patch(
            reverse("ad-detail", args=[ad_id]), {"title": "New"}, format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)
        # Owner can update pending
        self.authenticate(self.user)
        resp3 = self.client.patch(
            reverse("ad-detail", args=[ad_id]), {"title": "Updated"}, format="json"
        )
        self.assertEqual(resp3.status_code, status.HTTP_200_OK)
        # Approve as admin
        self.authenticate(self.admin)
        self.client.post(reverse("ad-approve", args=[ad_id]), {})
        # Owner can change price but not title
        self.authenticate(self.user)
        resp4 = self.client.patch(
            reverse("ad-detail", args=[ad_id]), {"title": "Nope"}, format="json"
        )
        self.assertEqual(resp4.status_code, status.HTTP_400_BAD_REQUEST)
        resp5 = self.client.patch(
            reverse("ad-detail", args=[ad_id]), {"monthly_rent": 2000}, format="json"
        )
        self.assertEqual(resp5.status_code, status.HTTP_200_OK)

    def test_filters_and_search(self):
        self.create_ad(title="Cheap", monthly_rent=1000, area_m2=30)
        self.create_ad(title="Expensive", monthly_rent=5000, area_m2=120)
        ad = Ad.objects.first()
        ad.status = AdStatus.APPROVED
        ad.save()
        ad2 = Ad.objects.last()
        ad2.status = AdStatus.APPROVED
        ad2.save()
        resp = self.client.get(
            self.list_url + "?min_price=2000&max_area=100&search=Cheap", format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 0)

    def test_throttle_limit(self):
        throttle_user = User.objects.create_user(
            email="throttle@example.com", full_name="Thr", password="StrongPass123"
        )
        self.authenticate(throttle_user)
        for i in range(10):
            data = {
                "title": f"A{i}",
                "description": "Desc",
                "monthly_rent": 1000,
                "property_type": "HOUSE",
                "bedrooms": 1,
                "bathrooms": 1,
                "area_m2": 50,
                "address": "Main",
                "latitude": 41.0,
                "longitude": 69.0,
                "images": [generate_image()],
            }
            resp = self.client.post(self.list_url, data, format="multipart")
            self.assertNotEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        data["title"] = "A10"
        resp = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_soft_delete_and_public_list(self):
        resp = self.create_ad(title="House 4")
        ad_id = resp.data["id"]
        self.authenticate(self.user)
        self.client.delete(reverse("ad-detail", args=[ad_id]))
        Ad.objects.filter(id=ad_id).update(status=AdStatus.APPROVED)
        resp2 = self.client.get(self.list_url)
        ids = [item["id"] for item in resp2.data.get("results", [])]
        self.assertNotIn(ad_id, ids)

    def test_owner_cannot_delete_approved(self):
        resp = self.create_ad(title="House 5")
        ad_id = resp.data["id"]
        self.authenticate(self.admin)
        self.client.post(reverse("ad-approve", args=[ad_id]), {})
        self.authenticate(self.user)
        resp2 = self.client.delete(reverse("ad-detail", args=[ad_id]))
        self.assertEqual(resp2.status_code, status.HTTP_403_FORBIDDEN)

    def test_location_required(self):
        self.authenticate(self.user)
        data = {
            "title": "No location",
            "description": "Desc",
            "monthly_rent": 1000,
            "property_type": "HOUSE",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_m2": 50,
            "address": "Main",
            "images": [generate_image()],
            "latitude": 41.0,
        }
        resp = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", resp.data)

    def test_coordinates_are_numbers(self):
        resp = self.create_ad(
            title="Coords",
            latitude=41.123456,
            longitude=69.987654,
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp_json = resp.json()
        self.assertIsInstance(resp_json["latitude"], float)
        self.assertEqual(resp_json["latitude"], 41.123456)
        self.assertIsInstance(resp_json["longitude"], float)

        list_resp = self.client.get(self.list_url)
        list_json = list_resp.json()
        self.assertIsInstance(list_json["results"][0]["latitude"], float)

        detail_resp = self.client.get(reverse("ad-detail", args=[resp_json["id"]]))
        detail_json = detail_resp.json()
        self.assertIsInstance(detail_json["latitude"], float)

    def test_stats_endpoint(self):
        self.create_ad(title="Available")
        available_ad = Ad.objects.latest("id")
        available_ad.status = AdStatus.APPROVED
        available_ad.save()

        self.create_ad(title="Pending")

        self.create_ad(title="Rented")
        rented_ad = Ad.objects.latest("id")
        rented_ad.status = AdStatus.ARCHIVED
        rented_ad.save()

        resp = self.client.get(reverse("ad-stats"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["available"], 1)
        self.assertEqual(resp.data["pending"], 1)
        self.assertEqual(resp.data["rented"], 1)
        self.assertEqual(resp.data["total"], 3)

    def test_owner_info_and_similar_endpoint(self):
        # Main ad
        resp = self.create_ad(title="Main")
        main_id = resp.data["id"]
        main_ad = Ad.objects.get(id=main_id)
        main_ad.status = AdStatus.APPROVED
        main_ad.save()

        # Additional ads
        similar_ids = []
        for title, ptype in [
            ("Sim1", "HOUSE"),
            ("Sim2", "HOUSE"),
            ("Sim3", "HOUSE"),
        ]:
            r = self.create_ad(title=title, property_type=ptype)
            ad = Ad.objects.get(id=r.data["id"])
            ad.status = AdStatus.APPROVED
            ad.save()
            similar_ids.append(ad.id)

        other_resp = self.create_ad(title="Other", property_type="APARTMENT")
        other_ad = Ad.objects.get(id=other_resp.data["id"])
        other_ad.status = AdStatus.APPROVED
        other_ad.save()

        # Similar endpoint
        resp_sim = self.client.get(reverse("ad-similar", args=[main_id]))
        self.assertEqual(resp_sim.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_sim.data), 3)
        returned_ids = {item["id"] for item in resp_sim.data}
        self.assertTrue(set(similar_ids).issubset(returned_ids))
        self.assertNotIn(other_ad.id, returned_ids)

        # Owner info on detail
        resp_detail = self.client.get(reverse("ad-detail", args=[main_id]))
        self.assertEqual(resp_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_detail.data["owner"]["full_name"], "User")
        self.assertEqual(resp_detail.data["owner"]["active_ads"], 5)

    def test_public_get_endpoints(self):
        resp = self.create_ad(title="Public")
        ad_id = resp.data["id"]
        self.client.force_authenticate(user=None)
        list_resp = self.client.get(self.list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in list_resp.data.get("results", [])]
        self.assertIn(ad_id, ids)
        detail_resp = self.client.get(reverse("ad-detail", args=[ad_id]))
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

    def test_locations_endpoint_returns_map_data(self):
        resp = self.create_ad(title="MapHouse", monthly_rent=1500, latitude=41.5, longitude=69.6)
        ad_id = resp.data["id"]
        self.client.force_authenticate(user=None)
        resp_loc = self.client.get(reverse("ad-locations"))
        self.assertEqual(resp_loc.status_code, status.HTTP_200_OK)
        data = resp_loc.json()
        self.assertEqual(len(data), 1)
        item = data[0]
        self.assertEqual(item["id"], ad_id)
        self.assertEqual(item["price"], 1500)
        self.assertIsInstance(item["latitude"], float)
        self.assertEqual(item["latitude"], 41.5)

    def test_my_ads_list_without_auth_is_empty(self):
        self.create_ad(title="Mine")
        self.client.force_authenticate(user=None)
        resp = self.client.get(reverse("my-ad-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("results", [])), 0)
