"""Test-wide environment guards.

Pytest imports this module before any test_*.py in this directory, so setting
env vars here runs before `main.py`'s `load_dotenv()` (dotenv defaults to
override=False — it never clobbers a var that's already set). Without this,
a developer's real .env (real SMTP creds for prod) leaks into the test
process, and registration tests send real verification emails — this has
already exhausted a real Gmail account's daily send quota once and 500'd
every test that hits /api/auth/register.
"""

import os

os.environ["SMTP_HOST"] = ""  # forces email_service.get_email_sender() -> ConsoleSender
os.environ.pop("CRAVINGS_ENV", None)  # don't let a real .env's prod flag trip _is_production()
os.environ.pop("BASE_PATH", None)  # ditto — BASE_PATH also signals prod in email_service._is_production()
