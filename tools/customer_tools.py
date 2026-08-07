def get_merchant_status(user_id: str) -> dict:
    """Mock boundary for an authenticated Getnet merchant API."""
    return {"user_id": user_id, "status": "active", "terminal_status": "online"}


def get_recent_settlements(user_id: str) -> list[dict]:
    """Return minimal settlement data without exposing banking secrets."""
    return [{"user_id": user_id, "sale_date": "ontem", "expected_in": "2 dias úteis"}]


def get_terminal_diagnostics(user_id: str) -> dict:
    """Mock terminal diagnostics used by the support specialist."""
    return {"user_id": user_id, "network": "unknown", "last_error": "none"}
