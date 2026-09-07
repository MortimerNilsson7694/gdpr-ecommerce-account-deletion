import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.account_deletion import CustomerAccount, DeleteAccountRequest, delete_account


class Captcha:
    def verify_captcha(self, token, ip):
        return {"ok": True, "data": {"verified": True}}


def test_deletion_revokes_sessions_and_orders_after_confirmation():
    account = CustomerAccount("cus_1", "a@example.test", [{"id": "ord_1"}], {"s1", "s2"})
    request = DeleteAccountRequest("cus_1", "tok", "203.0.113.4", "cus_1")
    result = delete_account(request, account, Captcha())
    assert result == {"status": 202, "state": "deleted", "user_id": "cus_1", "sessions_revoked": 2}
    assert account.deleted and not account.sessions and not account.orders
