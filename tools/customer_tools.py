def get_account_status(user_id: str) -> dict:
    """Mock boundary; replace with an authenticated account API."""
    return {"user_id": user_id, "status": "active", "transfer_limit": 5000}

def get_recent_activity(user_id: str) -> list[dict]:
    """Mock boundary; deliberately returns no sensitive account data."""
    return [{"user_id": user_id, "type": "transfer", "description": "nenhuma falha recente"}]
