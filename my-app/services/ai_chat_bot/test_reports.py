import unittest
from unittest.mock import AsyncMock, patch

from app.models.summary_models import AISummary, LeadAnalysis
from app.services import report_service
from app.services.email_service import normalize_gmail_app_password


class ReportServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_gmail_app_password_spaces_are_stripped(self):
        self.assertEqual(normalize_gmail_app_password("abcd efgh ijkl mnop"), "abcdefghijklmnop")

    async def test_generate_report_renders_enterprise_sections(self):
        ai_summary = AISummary(
            company_name="INDUX TECHNOLOGY",
            client_name="Rahul Sharma",
            client_phone_number="+919999999999",
            client_email="rahul@example.com",
            conversation_source="WhatsApp",
            language="Hindi / Hinglish",
            topic_of_discussion=["Client asked about pricing"],
            client_requirements=["WhatsApp chatbot"],
            lead_analysis=LeadAnalysis(
                lead_type="HOT LEAD",
                interest_level="High",
                buying_intent="Strong",
                estimated_closing_probability=85,
            ),
            ai_remarks="Recommended immediate follow-up within 24 hours.",
            next_actions=["Schedule demo meeting"],
            full_conversation_summary="Client is interested in AI automation.",
        )

        with (
            patch.object(report_service, "get_conversation_state", new=AsyncMock(return_value={"phone_number": "+919999999999"})),
            patch.object(
                report_service,
                "get_conversation_history",
                new=AsyncMock(return_value=[{"role": "user", "content": "Pricing kya hai?", "timestamp": "2026-05-13T19:45:00Z"}]),
            ),
            patch.object(report_service, "generate_ai_sales_summary", new=AsyncMock(return_value=ai_summary)),
            patch.object(report_service, "save_report", new=AsyncMock(side_effect=lambda report: report)),
        ):
            report = await report_service.generate_conversation_report(user_id="whatsapp:+919999999999")

        html = report_service.render_report_html(report)

        self.assertEqual(report.lead_analysis["lead_type"], "HOT LEAD")
        self.assertIn("SALES CONVERSATION REPORT", html)
        self.assertIn("INDUX TECHNOLOGY", html)
        self.assertIn("Rahul Sharma", html)
        self.assertIn("HOT LEAD", html)


if __name__ == "__main__":
    unittest.main()
