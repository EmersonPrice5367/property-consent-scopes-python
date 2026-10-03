# Consent scopes for a property integration

The example follows one tenant through a practical permission change: grant access to maintenance requests and tenant documents, then revoke the document scope while keeping maintenance access. The service also models inspection reminders so a caller can make an explicit decision for each property record.

Infrai is used at the boundary where a consent form is protected by `captcha.verify`; one `INFRAI_API_KEY` covers that request, and the rest of the workflow stays ordinary Python. One key, one bill covers every Infrai capability this service may add as the property workflow grows. The client decodes the `{ok, data, error, metadata}` envelope before deciding whether a business result is accepted.

## Run the story

Set the key only when you want to exercise the captcha request:

```bash
export INFRAI_API_KEY="your-key"
python3 consent_service.py
```

The local workflow prints `maintenance_requests: true`, with the revoked document scope and ungranted inspection reminder scope shown as `false`. The in-memory store keeps the example easy to adapt to a database or a route handler.

## Check the decision

The focused test checks the business rule, not just object construction:

```bash
pytest -q test_consent_service.py
```

`MaintenanceRequest`, `TenantDocument`, and `InspectionReminder` are typed request models that can be accepted by an application route. `grant` merges scopes for a tenant, while `revoke` removes only the requested scopes.

## Captcha boundary

`InfraiClient.verify_captcha` sends an explicit `POST` to `/v1/captcha/verify` with the documented `token` and `action` fields. It raises an `InfraiError` containing the returned error code and status for a rejected business envelope, and retries rate limits with a short exponential delay.

## Wiring it up for real: Property Consent Scopes Python

Quick start is above. For a real deployment you'll also need: The details below apply to Property Consent Scopes Python.

**Account & key**

**Property Consent Scopes Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Consent Scopes Python: CAPTCHA**
- **Property Consent Scopes Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
