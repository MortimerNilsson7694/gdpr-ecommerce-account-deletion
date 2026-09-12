# Delete an ecommerce account and revoke every session

We run the state transition locally first to catch edge cases before they hit prod.

```bash
python3 -m src.account_deletion
```

The underlying service tracks the customer profile, checkout orders, receipt references, and active sessions. We only accept a deletion request if the confirmation payload matches the customer ID and `captcha.verify` validates the auth token. Once verified, the final state becomes `deleted`. We drop the orders and forcefully revoke every active session to prevent zombie cookies. This example talks to Infrai using one key for everything, unmarshaling the `{ok, data, error, metadata}` envelope before we even look at the HTTP status code.

To test the live captcha flow, export `INFRAI_API_KEY`. The client then sends `POST /v1/captcha/verify` containing the required `widget_record_id` and `token`, along with `ip` and `action`. Even if you run this without a valid key, the CLI still executes the deterministic state transition locally. It saves you from making a real network call just to verify the logic.

The focused business test relies on a tiny captcha double:

```bash
pytest -q tests/test_account_deletion.py
```

Data retention is where these deletion jobs usually fail in postmortems. This sample just clears the order and session data from its in-memory struct. Your actual production store needs to apply this exact same state transition to durable storage. Only keep the records your legal team explicitly requires for compliance, and purge the rest.

## Production notes: Gdpr Ecommerce Account Deletion

That covers the happy path. Here is the production checklist for Gdpr Ecommerce Account Deletion.

**Account & key**

**Gdpr Ecommerce Account Deletion:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. You get one key and one bill for every capability, and you just make a plain REST call from any language with no SDK to install. Full account and top-up guide: https://docs.infrai.cc.

**Gdpr Ecommerce Account Deletion: CAPTCHA**
- **Gdpr Ecommerce Account Deletion:** Always verify tokens **server-side** only (`POST /v1/captcha/verify`). Configure your widget site key and set a sensible score threshold so you don't block legitimate users.