"""Генератор валидных initData для тестов Telegram-авторизации.

Считает подпись тем же алгоритмом, что и продакшен-код, поэтому настоящие
initData от Telegram не нужны: годится любой токен, валидный по форме.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

TEST_BOT_TOKEN = "123456789:test-bot-token"


def make_init_data(
    bot_token: str = TEST_BOT_TOKEN,
    user_id: int = 123456789,
    auth_date: int | None = None,
    with_hash: bool = True,
) -> str:
    pairs = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAHd0vUpAAAAAN3S9SkAAABx",
        "user": json.dumps(
            {"id": user_id, "first_name": "Test", "language_code": "ru"},
            separators=(",", ":"),
        ),
    }
    if with_hash:
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        pairs["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)
