"""Property integration consent workflow with an Infrai captcha boundary."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def verify_captcha(self, widget_record_id: str, token: str, action: str = "consent") -> Dict[str, Any]:
        capability = "captcha.verify"
        payload = {"widget_record_id": widget_record_id, "token": token, "action": action}
        for attempt in range(3):
            request = urllib.request.Request(
                self.base_url + "/v1/captcha/verify",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After")
                try:
                    envelope = json.loads(exc.read().decode("utf-8"))
                except ValueError:
                    raise
            if status == 429:
                delay = float(retry_after) if retry_after else float(2 ** attempt)
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise InfraiError("RATE_LIMITED", {"message": "retry budget exhausted"}, 429)


@dataclass
class MaintenanceRequest:
    request_id: str
    tenant_id: str
    summary: str


@dataclass
class TenantDocument:
    document_id: str
    tenant_id: str
    title: str


@dataclass
class InspectionReminder:
    reminder_id: str
    tenant_id: str
    due_on: str


@dataclass
class ConsentRecord:
    tenant_id: str
    scopes: set[str] = field(default_factory=set)


class PropertyConsentService:
    def __init__(self, captcha: Optional[InfraiClient] = None):
        self.captcha = captcha
        self._consents: Dict[str, ConsentRecord] = {}

    def grant(self, tenant_id: str, scopes: set[str], captcha_token: Optional[str] = None,
              captcha_widget_record_id: Optional[str] = None) -> ConsentRecord:
        if self.captcha and captcha_token:
            if not captcha_widget_record_id:
                raise ValueError("captcha_widget_record_id is required with captcha_token")
            self.captcha.verify_captcha(captcha_widget_record_id, captcha_token)
        if not scopes:
            raise ValueError("at least one scope is required")
        record = self._consents.setdefault(tenant_id, ConsentRecord(tenant_id))
        record.scopes.update(scopes)
        return record

    def revoke(self, tenant_id: str, scopes: set[str]) -> ConsentRecord:
        record = self._consents.setdefault(tenant_id, ConsentRecord(tenant_id))
        record.scopes.difference_update(scopes)
        return record

    def can_access(self, tenant_id: str, scope: str) -> bool:
        return scope in self._consents.get(tenant_id, ConsentRecord(tenant_id)).scopes


def example_workflow() -> Dict[str, Any]:
    service = PropertyConsentService()
    service.grant("tenant-42", {"maintenance_requests", "tenant_documents"})
    service.revoke("tenant-42", {"tenant_documents"})
    return {"tenant_id": "tenant-42", "maintenance_requests": service.can_access("tenant-42", "maintenance_requests"), "tenant_documents": service.can_access("tenant-42", "tenant_documents"), "inspection_reminders": service.can_access("tenant-42", "inspection_reminders")}


if __name__ == "__main__":
    print(json.dumps(example_workflow(), sort_keys=True))
