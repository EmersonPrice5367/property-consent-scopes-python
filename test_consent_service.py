import json
from unittest.mock import patch

from consent_service import InfraiClient, PropertyConsentService


def test_revoking_document_scope_keeps_maintenance_access():
    service = PropertyConsentService()
    service.grant("tenant-42", {"maintenance_requests", "tenant_documents"})
    service.revoke("tenant-42", {"tenant_documents"})
    assert service.can_access("tenant-42", "maintenance_requests") is True
    assert service.can_access("tenant-42", "tenant_documents") is False
    assert service.can_access("tenant-42", "inspection_reminders") is False


def test_captcha_request_includes_widget_record_id(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    response = type("Response", (), {
        "status": 200,
        "read": lambda self: b'{"ok": true, "data": {"valid": true}}',
        "__enter__": lambda self: self,
        "__exit__": lambda self, *args: None,
    })()

    with patch("urllib.request.urlopen", return_value=response) as urlopen:
        result = InfraiClient().verify_captcha("widget-123", "captcha-token")

    payload = json.loads(urlopen.call_args.args[0].data)
    assert payload == {
        "widget_record_id": "widget-123",
        "token": "captcha-token",
        "action": "consent",
    }
    assert result == {"valid": True}
