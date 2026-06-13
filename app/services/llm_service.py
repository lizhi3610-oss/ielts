import json
import time
import urllib.error
import urllib.request

from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER


def call_chat_completion(
    messages: list[dict[str, str]],
    max_tokens: int = 300,
    temperature: float = 0.4,
    max_retries: int = 1,
) -> str | None:
    """
    调用 OpenAI-compatible Chat Completions。

    没有配置或调用失败时返回 None，由业务层 fallback。
    """
    if not LLM_API_KEY:
        print(f"LLM is not configured. provider={LLM_PROVIDER}")
        return None

    base_url = LLM_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    data = None
    for attempt in range(max_retries + 1):
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")
            print(
                "LLM HTTP error. "
                f"provider={LLM_PROVIDER} model={LLM_MODEL} status={error.code} "
                f"attempt={attempt + 1} detail={detail}"
            )
            if 400 <= error.code < 500 and error.code != 429:
                return None
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            print(
                "LLM call failed. "
                f"provider={LLM_PROVIDER} model={LLM_MODEL} "
                f"attempt={attempt + 1} error={error}"
            )

        if attempt < max_retries:
            time.sleep(0.5)

    if data is None:
        return None

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None

    if not isinstance(content, str):
        return None

    return content.strip() or None
