import unittest
from datetime import datetime, timezone
from unittest import mock

import requests

import bonds


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, *, get_response=None, post_response=None):
        self.get_response = get_response
        self.post_response = post_response
        self.get_call = None
        self.post_call = None

    def get(self, url, **kwargs):
        self.get_call = (url, kwargs)
        return self.get_response

    def post(self, url, **kwargs):
        self.post_call = (url, kwargs)
        return self.post_response


class BondCalendarTests(unittest.TestCase):
    def test_get_bond_calendar_uses_json_api(self):
        expected = [{"SECURITY_CODE": "123456"}]
        session = FakeSession(
            get_response=FakeResponse({"result": {"data": expected}})
        )

        actual = bonds.get_bond_calendar(session=session)

        self.assertEqual(actual, expected)
        _, request_options = session.get_call
        self.assertNotIn("callback", request_options["params"])
        self.assertEqual(request_options["timeout"], bonds.REQUEST_TIMEOUT)

    def test_get_bond_calendar_rejects_invalid_schema(self):
        session = FakeSession(get_response=FakeResponse({"success": True}))

        with self.assertRaisesRegex(RuntimeError, "result"):
            bonds.get_bond_calendar(session=session)

    def test_get_bond_calendar_rejects_missing_data(self):
        session = FakeSession(get_response=FakeResponse({"result": {"data": None}}))

        with self.assertRaisesRegex(RuntimeError, "result.data"):
            bonds.get_bond_calendar(session=session)

    def test_bonds_for_date_accepts_timestamp_and_date(self):
        calendar = [
            {"SECURITY_CODE": "1", "PUBLIC_START_DATE": "2026-08-20 00:00:00"},
            {"SECURITY_CODE": "2", "PUBLIC_START_DATE": "2026-08-20"},
            {"SECURITY_CODE": "3", "PUBLIC_START_DATE": "2026-08-21 00:00:00"},
            {"SECURITY_CODE": "4"},
        ]

        selected = bonds.bonds_for_date(calendar, "2026-08-20")

        self.assertEqual([bond["SECURITY_CODE"] for bond in selected], ["1", "2"])

    def test_get_today_date_converts_to_beijing_time(self):
        utc_time = datetime(2026, 8, 19, 16, 30, tzinfo=timezone.utc)

        self.assertEqual(bonds.get_today_date(utc_time), "2026-08-20")

    def test_send_to_wechat_checks_application_error(self):
        session = FakeSession(
            post_response=FakeResponse({"code": 40001, "message": "invalid key"})
        )

        with self.assertRaisesRegex(RuntimeError, "invalid key"):
            bonds.send_to_wechat([], server_key="secret", session=session)

        url, request_options = session.post_call
        self.assertEqual(url, "https://sctapi.ftqq.com/secret.send")
        self.assertEqual(request_options["timeout"], bonds.REQUEST_TIMEOUT)

    def test_send_to_wechat_hides_key_on_http_error(self):
        session = FakeSession(post_response=FakeResponse({}, status_code=500))

        with self.assertRaisesRegex(RuntimeError, r"status=500") as error:
            bonds.send_to_wechat([], server_key="very-secret", session=session)

        self.assertNotIn("very-secret", str(error.exception))

    def test_send_to_wechat_requires_server_key(self):
        with self.assertRaisesRegex(RuntimeError, "SERVERCHAN_API_KEY"):
            bonds.send_to_wechat([], server_key="")

    def test_env_flag_rejects_invalid_value(self):
        with mock.patch.dict("os.environ", {"NOTIFY_WHEN_EMPTY": "maybe"}):
            with self.assertRaisesRegex(RuntimeError, "true 或 false"):
                bonds.env_flag("NOTIFY_WHEN_EMPTY")


if __name__ == "__main__":
    unittest.main()
