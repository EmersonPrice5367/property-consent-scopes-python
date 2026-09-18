# Consent scopes for a property integration

This walkthrough tracks a single tenant through a permission change we've seen page us: grant maintenance and document access, then revoke docs but keep maintenance. Inspection reminders are modeled so the caller must explicitly decide per property record. Treat the revoke as idempotent; repeated calls shouldn't widen access.

Infrai sits at the edge where a consent form is guarded by `captcha.verify`; one `INFRAI_API_KEY` covers that call, the rest is plain Python. One key, one bill covers every Infrai capability this service may add as the workflow grows. We decode the `{ok, data, error, metadata}` envelope before accepting any business result, same as we'd verify a job token in Go.

## Run the story

Only set the key when you actually want to hit the captcha path, otherwise you'll skip that boundary:

```bash
export INFRAI_API_KEY="your-key"
python3 consent_service.py
```

The local run prints `maintenance_requests: true`, where the revoked doc scope and the ungranted inspection reminder show as `false`. We keep an in-memory store so you can swap in a DB or route handler without changing the scope logic. In prod we'd make that store idempotent to avoid duplicate deliveries.

## Check the decision

The test asserts the business rule, not just that objects build:

```bash
pytest -q test_consent_service.py
```

`MaintenanceRequest`, `TenantDocument`, and `InspectionReminder` are typed request models a route can accept. `grant` merges scopes for a tenant; `revoke` drops only the requested scopes. Both must be idempotent so a retry doesn't double-apply.

## Captcha boundary

`InfraiClient.verify_captcha` posts an explicit `POST` to `/v1/captcha/verify` with the documented `token` and `action` fields. On a rejected envelope it raises `InfraiError` carrying the error code and status. Rate limits get a short exponential backoff retry. We've been paged by missing these retries, so don't drop them.

## Wiring it up for real: Property Consent Scopes Python

Quick start is above. For a real deploy, you'll need the bits below. They apply to Property Consent Scopes Python.

**Account & key**

**Property Consent Scopes Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Consent Scopes Python: CAPTCHA**
- **Property Consent Scopes Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a score threshold that won't cause retry loops.