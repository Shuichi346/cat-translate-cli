"""サーバーへの翻訳リクエストを送るHTTPクライアント"""

from __future__ import annotations

import httpx


DEFAULT_SERVER_URL = "http://127.0.0.1:7860"
HEALTH_TIMEOUT = 1.0
TRANSLATE_TIMEOUT = 120.0


def is_server_running(server_url: str = DEFAULT_SERVER_URL) -> bool:
    """サーバーが起動中かどうか確認する"""
    try:
        response = httpx.get(
            f"{server_url}/api/translate",
            timeout=HEALTH_TIMEOUT,
        )
        # Gradio API エンドポイントが存在すれば 200 以外でも起動中と判定
        return response.status_code != 404
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        return False


def translate_via_server(
    text: str,
    src_lang: str | None = None,
    tgt_lang: str | None = None,
    server_url: str = DEFAULT_SERVER_URL,
) -> str:
    """サーバー経由で翻訳する（Gradio API を呼び出す）"""
    payload = {
        "data": [
            text,
            src_lang if src_lang else "自動判定",
            tgt_lang if tgt_lang else "自動判定",
        ],
    }

    try:
        response = httpx.post(
            f"{server_url}/api/translate",
            json=payload,
            timeout=TRANSLATE_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.ConnectError as error:
        raise RuntimeError(
            f"サーバーに接続できません ({server_url}): {error}"
        ) from error
    except httpx.HTTPStatusError as error:
        raise RuntimeError(
            f"サーバーからエラーが返されました: {error}"
        ) from error
    except httpx.TimeoutException as error:
        raise RuntimeError(
            f"サーバーからの応答がタイムアウトしました: {error}"
        ) from error

    result = response.json()
    data = result.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("サーバー応答の形式が不正です。")

    translated = data[0]
    if not isinstance(translated, str) or not translated.strip():
        raise RuntimeError("サーバーから翻訳結果を取得できませんでした。")

    return translated.strip()
