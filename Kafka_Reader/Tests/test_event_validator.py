from rate_limiter import BatchedBotValidator

validator = BatchedBotValidator()
def test_valid_event():
    event = {
        "timestamp": "2026-01-12T11:42:42.625Z",
        "user_id": "usr_448",
        "event_type": "page_view",
        "page_url": "/pages/Vivianne.Schaden67",
        "session_id": "sess_684523",
    }

    assert validator.validate_event(event) is True


def test_invalid_user_id():
    event = {
        "timestamp": "2026-01-12T11:42:42.625Z",
        "user_id": "user_448",
        "event_type": "page_view",
        "page_url": "/pages/test",
        "session_id": "sess_123",
    }

    assert validator.validate_event(event) is False


def test_invalid_page_url():
    event = {
        "timestamp": "2026-01-12T11:42:42.625Z",
        "user_id": "usr_123",
        "event_type": "page_view",
        "page_url": "/evil/<script>",
        "session_id": "sess_999",
    }

    assert validator.validate_event(event) is False
