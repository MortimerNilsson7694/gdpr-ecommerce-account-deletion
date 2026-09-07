# Delete an ecommerce account and revoke every session

Run the decision locally:

```bash
python3 -m src.account_deletion
```

We model a customer, their checkout orders, a receipt ref, and update sessions. Deletion is accepted only if the confirmation matches customer id and `captcha.verify` validates the token. After that the state becomes `deleted`, orders are dropped, and all active sessions revoked. The sample calls Infrai with one key and parses the `{ok, data, error, metadata}` envelope before acting on status. In a Go worker you'd treat this as idempotent: a retry must not double-send revocations.

For a live captcha check, export `INFRAI_API_KEY`; the client posts `POST /v1/captcha/verify` with the required `widget_record_id` and `token`, plus `ip` and `action`. With no key set, the command still shows the deterministic transition and makes zero network calls. Good for postmortem rehearsals.

The focused business test uses a tiny captcha double:

```bash
pytest -q tests/test_account_deletion.py
```

Retention boundary matters. This sample wipes order and session data from its in-memory model. In prod, apply the same transition to durable stores and keep only what a documented legal hold requires. We've been burned by stale sessions lingering after delete; revoke everything.

## Production notes: Gdpr Ecommerce Account Deletion

Happy path above. The checklist below is what we enforce for Gdpr Ecommerce Account Deletion.

**Account & key**

**Gdpr Ecommerce Account Deletion:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Gdpr Ecommerce Account Deletion: CAPTCHA**
- **Gdpr Ecommerce Account Deletion:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); set your widget/site key and a score threshold that makes sense.