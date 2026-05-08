import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.tools import crm_tool
from app.tools.crm_tool import (
    add_note,
    close_hubspot_client,
    create_lead,
    get_contact,
    update_customer,
    update_lead_status,
)


class CRMToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = AsyncMock()
        self.client_patch = patch.object(crm_tool, "_get_hubspot_client", return_value=self.client)
        self.client_patch.start()

    def tearDown(self):
        self.client_patch.stop()

    def _response(self, status_code: int, data: dict):
        request = httpx.Request("GET", "https://api.hubapi.com/test")
        return httpx.Response(status_code, json=data, request=request)

    async def test_create_lead_posts_contact_properties(self):
        self.client.request.return_value = self._response(201, {"id": "123", "properties": {"email": "a@test.com"}})

        result = await create_lead(
            name="Akshat Seth",
            email="a@test.com",
            phone="+10000000000",
            lead_status="NEW",
        )

        self.assertTrue(result["success"])
        self.client.request.assert_awaited_once()
        _, path = self.client.request.await_args.args[:2]
        payload = self.client.request.await_args.kwargs["json"]
        self.assertEqual(path, "/crm/v3/objects/contacts")
        self.assertEqual(payload["properties"]["firstname"], "Akshat")
        self.assertEqual(payload["properties"]["lastname"], "Seth")
        self.assertEqual(payload["properties"]["hs_lead_status"], "NEW")

    async def test_update_customer_by_email(self):
        self.client.request.return_value = self._response(200, {"id": "123"})

        result = await update_customer(email="a@test.com", lead_status="QUALIFIED")

        self.assertTrue(result["success"])
        self.assertEqual(self.client.request.await_args.args[0], "PATCH")
        self.assertEqual(self.client.request.await_args.args[1], "/crm/v3/objects/contacts/a@test.com")
        self.assertEqual(self.client.request.await_args.kwargs["params"], {"idProperty": "email"})

    async def test_add_note_associates_note_with_contact(self):
        self.client.request.return_value = self._response(201, {"id": "note-123"})

        result = await add_note(contact_id="123", note="AI summary")

        self.assertTrue(result["success"])
        payload = self.client.request.await_args.kwargs["json"]
        self.assertEqual(payload["properties"]["hs_note_body"], "AI summary")
        self.assertEqual(payload["associations"][0]["to"]["id"], "123")

    async def test_get_contact_by_email(self):
        self.client.request.return_value = self._response(200, {"id": "123"})

        result = await get_contact(email="a@test.com")

        self.assertTrue(result["success"])
        self.assertEqual(self.client.request.await_args.args[0], "GET")
        self.assertEqual(self.client.request.await_args.kwargs["params"]["idProperty"], "email")

    async def test_update_lead_status_delegates_to_update_customer(self):
        self.client.request.return_value = self._response(200, {"id": "123"})

        result = await update_lead_status(email="a@test.com", lead_status="CONNECTED")

        self.assertTrue(result["success"])
        payload = self.client.request.await_args.kwargs["json"]
        self.assertEqual(payload["properties"]["hs_lead_status"], "CONNECTED")

    async def test_request_retries_rate_limits(self):
        self.client.request.side_effect = [
            self._response(429, {"message": "rate limited"}),
            self._response(200, {"id": "123"}),
        ]

        with (
            patch.object(crm_tool.asyncio, "sleep", new=AsyncMock()),
            patch.object(crm_tool.logger, "warning"),
        ):
            result = await get_contact(contact_id="123")

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)

    async def test_request_returns_structured_error(self):
        self.client.request.return_value = self._response(400, {"message": "bad request"})

        with patch.object(crm_tool.logger, "warning"), patch.object(crm_tool.logger, "error"):
            result = await get_contact(contact_id="123")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "HTTPStatusError")

    async def test_close_hubspot_client(self):
        client = MagicMock()
        client.aclose = AsyncMock()
        crm_tool._hubspot_client = client

        await close_hubspot_client()

        client.aclose.assert_awaited_once()
        self.assertIsNone(crm_tool._hubspot_client)


if __name__ == "__main__":
    unittest.main()
