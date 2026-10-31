from rest_framework.test import APITestCase

from .models import HuntLog, WantedCriminal


class SeedTests(APITestCase):
    def test_database_is_prefilled(self):
        self.assertGreaterEqual(WantedCriminal.objects.count(), 5)
        self.assertGreaterEqual(HuntLog.objects.count(), 10)

    def test_one_to_many_relationship(self):
        criminal = WantedCriminal.objects.get(nickname="Slippery Lio")
        self.assertEqual(criminal.hunts.count(), 3)


class CriminalApiTests(APITestCase):
    def test_list_returns_plain_array(self):
        r = self.client.get("/api/criminals/")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json(), list)
        self.assertEqual(len(r.json()), 6)

    def test_detail_and_404(self):
        r = self.client.get("/api/criminals/1/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nickname"], "Black Comet")
        self.assertEqual(r.json()["last_known_coordinates"], {"latitude": 15.5, "longitude": -42.3})
        self.assertEqual(self.client.get("/api/criminals/999999/").status_code, 404)
        self.assertEqual(self.client.get("/api/criminals/abc/").status_code, 404)

    def test_unknown_name_and_note_only_location(self):
        data = self.client.get("/api/criminals/2/").json()
        self.assertIsNone(data["name"])
        self.assertIsNone(data["last_known_coordinates"])
        self.assertTrue(data["location_note"])

    def test_min_and_max_reward(self):
        r = self.client.get("/api/criminals/?min_reward=10000").json()
        self.assertEqual({c["nickname"] for c in r}, {"Black Comet", "The Ghost", "Slippery Lio"})
        r = self.client.get("/api/criminals/?max_reward=3200").json()
        self.assertEqual({c["nickname"] for c in r}, {"Iron Jaw", "Pixel"})
        r = self.client.get("/api/criminals/?min_reward=3200&max_reward=7500").json()
        self.assertEqual({c["nickname"] for c in r}, {"Iron Jaw", "Red Siren"})

    def test_boolean_filters(self):
        r = self.client.get("/api/criminals/?armed=true").json()
        self.assertEqual({c["nickname"] for c in r}, {"Black Comet", "Red Siren", "Iron Jaw"})
        r = self.client.get("/api/criminals/?armed=false").json()
        self.assertEqual(len(r), 3)
        r = self.client.get("/api/criminals/?has_crew=true").json()
        self.assertEqual({c["nickname"] for c in r}, {"Black Comet", "Iron Jaw", "Slippery Lio"})
        r = self.client.get("/api/criminals/?escape_master=true").json()
        self.assertEqual({c["nickname"] for c in r}, {"Black Comet", "The Ghost", "Slippery Lio"})

    def test_filters_work_together_with_sort(self):
        r = self.client.get("/api/criminals/?min_reward=5000&armed=true&sort=-reward").json()
        self.assertEqual([c["nickname"] for c in r], ["Black Comet", "Red Siren"])
        r = self.client.get("/api/criminals/?armed=true&has_crew=true&escape_master=true").json()
        self.assertEqual([c["nickname"] for c in r], ["Black Comet"])

    def test_sort_by_reward(self):
        asc = [c["reward"] for c in self.client.get("/api/criminals/?sort=reward").json()]
        desc = [c["reward"] for c in self.client.get("/api/criminals/?sort=-reward").json()]
        self.assertEqual(asc, sorted(asc, key=float))
        self.assertEqual(desc, sorted(desc, key=float, reverse=True))
        self.assertEqual(asc[0], "1800.00")
        self.assertEqual(desc[0], "50000.00")

    def test_invalid_query_parameters_return_400(self):
        self.assertEqual(self.client.get("/api/criminals/?sort=name").status_code, 400)
        self.assertEqual(self.client.get("/api/criminals/?min_reward=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/criminals/?armed=maybe").status_code, 400)

    def test_criminals_are_read_only(self):
        self.assertEqual(self.client.post("/api/criminals/", {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete("/api/criminals/1/").status_code, 405)


class HuntApiTests(APITestCase):
    def test_list_and_filter_by_criminal(self):
        self.assertEqual(len(self.client.get("/api/hunts/").json()), 12)
        r = self.client.get("/api/hunts/?criminal_id=5").json()
        self.assertEqual(len(r), 3)
        self.assertTrue(all(h["criminal_id"] == 5 for h in r))
        self.assertEqual(self.client.get("/api/hunts/?criminal_id=6").json(), [])
        self.assertEqual(self.client.get("/api/hunts/?criminal_id=abc").status_code, 400)

    def test_create_read_update_delete(self):
        body = {"criminal_id": 3, "success": False, "notes": "Target escaped through an asteroid field."}
        r = self.client.post("/api/hunts/", body, format="json")
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertEqual(data["criminal_id"], 3)
        self.assertIsNotNone(data["created_at"])
        hid = data["id"]

        self.assertEqual(self.client.get(f"/api/hunts/{hid}/").json()["notes"], body["notes"])

        r = self.client.patch(f"/api/hunts/{hid}/", {"success": True, "notes": "Caught later."}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])
        self.assertEqual(r.json()["notes"], "Caught later.")
        self.assertEqual(r.json()["created_at"], data["created_at"])

        self.assertEqual(self.client.delete(f"/api/hunts/{hid}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/hunts/{hid}/").status_code, 404)

    def test_created_at_is_set_by_server(self):
        body = {
            "criminal_id": 1, "success": True, "notes": "x",
            "created_at": "2000-01-01T00:00:00Z", "id": 999,
        }
        data = self.client.post("/api/hunts/", body, format="json").json()
        self.assertFalse(data["created_at"].startswith("2000"))
        self.assertNotEqual(data["id"], 999)

    def test_criminal_must_exist(self):
        r = self.client.post("/api/hunts/", {"criminal_id": 9999, "success": False, "notes": "x"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("criminal_id", r.json())

    def test_validation_errors(self):
        post = lambda body: self.client.post("/api/hunts/", body, format="json")
        self.assertEqual(post({"success": False, "notes": "x"}).status_code, 400)  # нет criminal_id
        self.assertEqual(post({"criminal_id": 1, "success": False}).status_code, 400)  # нет notes
        self.assertEqual(post({"criminal_id": 1, "success": False, "notes": "  "}).status_code, 400)
        self.assertEqual(post({"criminal_id": 1, "success": "banana", "notes": "x"}).status_code, 400)
        self.assertEqual(post({"criminal_id": "abc", "success": False, "notes": "x"}).status_code, 400)

    def test_invalid_ids_return_404(self):
        self.assertEqual(self.client.get("/api/hunts/999999/").status_code, 404)
        self.assertEqual(self.client.get("/api/hunts/abc/").status_code, 404)
        self.assertEqual(self.client.patch("/api/hunts/999999/", {"notes": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete("/api/hunts/999999/").status_code, 404)

    def test_cannot_change_criminal_and_put_not_allowed(self):
        hid = HuntLog.objects.first().id
        r = self.client.patch(f"/api/hunts/{hid}/", {"criminal_id": 6}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.put(f"/api/hunts/{hid}/", {"criminal_id": 1, "success": True, "notes": "x"}, format="json")
        self.assertEqual(r.status_code, 405)

    def test_health(self):
        self.assertEqual(self.client.get("/health/").json()["status"], "ok")
