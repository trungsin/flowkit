"""One reading of a request's error text, shared by the worker and the API.

The worker decides from the class whether to retry; ``/api/requests/batch-status``
and ``/api/requests/retry-failed`` report and requeue by the same class, so a
client sees exactly why the worker stopped.

Order matters: the local hold message also names PUBLIC_ERROR_UNUSUAL_ACTIVITY,
and Google's unusual-activity answer can also mention reCAPTCHA.
"""
from __future__ import annotations

# Never reached Google: FlowClient refused the submit while a hold was active.
FLOW_HOLD = "flow_hold"
# Google refused the session (PUBLIC_ERROR_UNUSUAL_ACTIVITY).
ACCOUNT_BLOCKED = "account_blocked"
# The reCAPTCHA bypass failed ([HIJACK] extension_hijack_detected).
CAPTCHA_HIJACK = "captcha_hijack"
# A capability or setting the request cannot get past by being resent.
CONFIG = "config"
# The prompt tripped Google's safety filter; resend only after changing it.
CONTENT_POLICY = "content_policy"
# Daily credits are gone.
QUOTA = "quota"
# The Chrome extension dropped or reconnected mid-request.
EXTENSION = "extension"
# The reCAPTCHA token could not be minted.
CAPTCHA = "captcha"
# Anything else: backend 500s, polling timeouts, network.
TRANSIENT = "transient"

# Classes that stop every Flow client until a human has checked the Flow UI.
ACCOUNT_SAFETY = frozenset({ACCOUNT_BLOCKED, CAPTCHA_HIJACK})
ALL_CLASSES = frozenset({
    FLOW_HOLD, ACCOUNT_BLOCKED, CAPTCHA_HIJACK, CONFIG, CONTENT_POLICY,
    QUOTA, EXTENSION, CAPTCHA, TRANSIENT,
})
# Classes the worker never resends on its own.
TERMINAL = frozenset({FLOW_HOLD, ACCOUNT_BLOCKED, CONFIG, CONTENT_POLICY, QUOTA})
# Classes ``retry-failed`` requeues when the caller names none.
REQUEUE_BY_DEFAULT = frozenset({FLOW_HOLD, TRANSIENT, CAPTCHA, EXTENSION})


def classify_error(message: str | None) -> str:
    text = (message or "").lower()
    if "local cooldown active" in text:
        return FLOW_HOLD
    if "[hijack]" in text or "extension_hijack" in text:
        return CAPTCHA_HIJACK
    if "unusual_activity" in text or "unusual activity" in text:
        return ACCOUNT_BLOCKED
    if ("unsupported_on_batch_api" in text or "no_flow_project" in text
            or "model_access_denied" in text):
        return CONFIG
    if "unsafe_generation" in text:
        return CONTENT_POLICY
    if "user_quota_reached" in text:
        return QUOTA
    if ("extension reconnected" in text or "extension disconnected" in text
            or "extension not connected" in text):
        return EXTENSION
    if "captcha" in text:
        return CAPTCHA
    return TRANSIENT
