from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
API_CENTER = ROOT.parent
sys.path.insert(0, str(API_CENTER))
SPEC = importlib.util.spec_from_file_location("opensky_network_task", ROOT / "opensky_network_task.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class OpenSkyProviderTests(unittest.TestCase):
    def test_catalog_contract(self):
        provider = json.loads((ROOT / "provider-catalog.json").read_text(encoding="utf-8"))["providers"][0]
        self.assertEqual(provider["provider_id"], "opensky-network")
        self.assertEqual(provider["ticket_prefix"], "[intel-opensky]")
        self.assertEqual(provider["required_secret_environment_variable"], "OPEN_SKY_CLIENT_SECRET")
        self.assertEqual(provider["required_repository_variable"], "OPEN_SKY_CLIENT_ID")
        self.assertEqual(len(provider["operations"]), 9)
        self.assertFalse(provider["limits"]["global_state_query_allowed"])
        self.assertFalse(provider["limits"]["trino_historical_access_allowed"])
        self.assertTrue(all(row["result_contract"]["read_only"] for row in provider["operations"]))

    def test_current_states_require_a_filter(self):
        with self.assertRaisesRegex(ValueError, "require an ICAO24 filter"):
            MODULE.build_request("states-current", {})
        path, query, auth = MODULE.build_request(
            "states-current", {"icao24": ["A0B1C2"], "extended": True}
        )
        self.assertEqual(path, "/api/states/all")
        self.assertIn(("icao24", "a0b1c2"), query)
        self.assertIn(("extended", "1"), query)
        self.assertFalse(auth)

    def test_bbox_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "400 square degrees"):
            MODULE.build_request(
                "states-current", {"lamin": 0, "lomin": 0, "lamax": 30, "lomax": 30}
            )
        _, query, _ = MODULE.build_request(
            "states-current", {"lamin": 25.8, "lomin": 118.9, "lamax": 26.3, "lomax": 119.6}
        )
        self.assertIn(("lamin", "25.8"), query)

    def test_recent_states_are_one_hour_only(self):
        now = int(time.time())
        _, query, auth = MODULE.build_request(
            "states-recent", {"icao24": ["abc123"], "time": now - 120}
        )
        self.assertTrue(auth)
        self.assertIn(("time", str(now - 120)), query)
        with self.assertRaisesRegex(ValueError, "last hour"):
            MODULE.build_request("states-recent", {"icao24": ["abc123"], "time": now - 7200})

    def test_flight_interval_limits(self):
        now = int(time.time())
        _, query, auth = MODULE.build_request(
            "flights-interval", {"begin": now - 3600, "end": now - 10}
        )
        self.assertTrue(auth)
        self.assertEqual(dict(query)["begin"], str(now - 3600))
        with self.assertRaisesRegex(ValueError, "7200 seconds"):
            MODULE.build_request("flights-interval", {"begin": now - 8000, "end": now - 10})

    def test_airport_and_track_validation(self):
        past_day = int(time.time()) - 2 * 86400
        path, _, _ = MODULE.build_request(
            "airport-arrivals", {"airport": "zsfz", "begin": past_day, "end": past_day + 3600}
        )
        self.assertEqual(path, "/api/flights/arrival")
        with self.assertRaisesRegex(ValueError, "four-character"):
            MODULE.build_request(
                "airport-departures", {"airport": "FZ", "begin": past_day, "end": past_day + 3600}
            )
        path, query, _ = MODULE.build_request("track-aircraft", {"icao24": ["ABC123"], "time": 0})
        self.assertEqual(path, "/api/tracks/all")
        self.assertIn(("icao24", "abc123"), query)

    def test_credentials_must_be_paired(self):
        with patch.dict(os.environ, {"OPEN_SKY_CLIENT_ID": "client", "OPEN_SKY_CLIENT_SECRET": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "configured together"):
                MODULE._credentials()

    @patch.object(MODULE.requests, "post")
    @patch.object(MODULE.requests, "get")
    def test_oauth_and_response_never_persist_secrets(self, get_mock, post_mock):
        token = "very-secret-access-token"
        post_response = Mock()
        post_response.ok = True
        post_response.status_code = 200
        post_response.content = json.dumps({"access_token": token, "expires_in": 1800}).encode()
        post_response.json.return_value = {"access_token": token, "expires_in": 1800}
        post_mock.return_value = post_response
        get_response = Mock()
        get_response.ok = True
        get_response.status_code = 200
        get_response.content = json.dumps({"time": 1, "states": [["abc123", token]]}).encode()
        get_response.json.return_value = {"time": 1, "states": [["abc123", token]]}
        get_response.headers = {"Content-Type": "application/json", "X-Rate-Limit-Remaining": "3999"}
        get_mock.return_value = get_response
        self.assertEqual(MODULE._token("client", "secret", 10), token)
        clean = MODULE._scrub(get_response.json(), ["secret", token])
        self.assertNotIn(token, json.dumps(clean))
        self.assertIn("[REDACTED]", json.dumps(clean))

    def test_404_flight_contract_is_empty(self):
        self.assertEqual(MODULE._row_count("flights-aircraft", []), 0)


if __name__ == "__main__":
    unittest.main()
