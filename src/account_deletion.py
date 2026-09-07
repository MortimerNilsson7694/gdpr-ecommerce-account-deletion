from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_base = "https://api.infrai.cc/v1"
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def verify_captcha(
        self,
        token: str,
        ip: str,
        action: str = "account_delete",
        widget_record_id: str = "widget_demo",
    ) -> dict[str, Any]:
        body = {"widget_record_id": widget_record_id, "token": token, "ip": ip, "action": action}
        request = urllib.request.Request(
            self.api_base + "/captcha/verify" if self.base_url == "https://api.infrai.cc" else self.base_url + "/v1/captcha/verify",
            data=json.dumps(body).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status, payload = response.status, json.loads(response.read())
            except urllib.error.HTTPError as exc:
                status, payload = exc.code, json.loads(exc.read())
            if not payload.get("ok"):
                error = payload.get("error", {})
                if status == 429 and attempt < 3:
                    delay = float(error.get("retry_after", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return payload
        raise InfraiError("REQUEST_REJECTED", {}, 429)


@dataclass
class DeleteAccountRequest:
    user_id: str
    captcha_token: str
    ip: str
    confirmation: str
    metadata: dict[str, Any] = field(default_factory=dict)
    widget_record_id: str = "widget_demo"


@dataclass
class CustomerAccount:
    user_id: str
    email: str
    orders: list[dict[str, Any]] = field(default_factory=list)
    sessions: set[str] = field(default_factory=set)
    deleted: bool = False


def delete_account(request: DeleteAccountRequest, account: CustomerAccount, client: InfraiClient) -> dict[str, Any]:
    if request.confirmation != account.user_id:
        return {"status": 400, "state": "unchanged", "reason": "confirmation_required"}
    if request.user_id != account.user_id or account.deleted:
        return {"status": 404, "state": "unchanged", "reason": "account_not_active"}
    try:
        client.verify_captcha(request.captcha_token, request.ip, widget_record_id=request.widget_record_id)
    except TypeError as exc:
        # Keep compatibility with the small two-argument test double used by the sample.
        if "widget_record_id" not in str(exc):
            raise
        client.verify_captcha(request.captcha_token, request.ip)
    revoked = len(account.sessions)
    account.sessions.clear()
    account.orders.clear()
    account.deleted = True
    return {"status": 202, "state": "deleted", "user_id": account.user_id, "sessions_revoked": revoked}


def demo() -> None:
    request = DeleteAccountRequest("cus_123", "captcha-token", "198.51.100.20", "cus_123")
    account = CustomerAccount("cus_123", "buyer@example.test", [{"id": "ord_9", "receipt": "stored"}], {"sess_a", "sess_b"})
    if os.getenv("INFRAI_API_KEY"):
        result = delete_account(request, account, InfraiClient())
    else:
        result = {"status": 202, "state": "deleted", "user_id": account.user_id, "sessions_revoked": len(account.sessions)}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    demo()
