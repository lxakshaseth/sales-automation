from app.core.logger import log_action, log_error, log_event, log_info, set_request_id


def main() -> None:
    set_request_id("example-request-id")
    log_info("Email sent", provider="resend", user_id="demo-user-001")
    log_error("WhatsApp timeout", provider="whatsapp", user_id="demo-user-001")
    log_action("create_lead", user_id="demo-user-001", tool="hubspot")
    log_event("appointment_booked", user_id="demo-user-001", meeting_link="https://meet.google.com/demo")


if __name__ == "__main__":
    main()
