import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path

logger = logging.getLogger("OpencodeClient")

def get_opencode_key() -> str:
    key = os.environ.get("OPENCODE_ZEN_API_KEY") or os.environ.get("OPENCODE_API_KEY")
    if key:
        return key.strip()
    
    candidates = [
        Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes\.env")),
        Path(__file__).parent / ".env",
        Path.cwd() / ".env"
    ]
    for p in candidates:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("OPENCODE_ZEN_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("'\"")
            except Exception:
                pass
    return "oc_sk_927379dbbd11_HAmLjjZQNY2eABc9nZO2xw9fP3nFAoOi"

def call_opencode_chat(
    prompt: str,
    system_prompt: str = "",
    model: str = "deepseek-v4.1-flash",
    max_tokens: int = 8192,
    timeout: int = 180
) -> tuple[str, dict]:
    """
    Calls OpenCode Zen API with DeepSeek V4.1 Flash model.
    Guarantees clean final content without internal reasoning clutter.
    Uses 8192 max_tokens so reasoning (CoT) and complete final answer never get truncated.
    """
    api_key = get_opencode_key()
    base_url = os.environ.get("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)"
    }
    
    sys_content = system_prompt or (
        "Kamu adalah asisten profesional Pegawai AI PT AI Top Trends. "
        "Fokuskan penalaran singkat di awal, lalu berikan jawaban akhir lengkap, terstruktur, "
        "dan tuntas dalam bahasa Indonesia tanpa terpotong."
    )
    
    messages = [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": prompt}
    ]
    
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            content = msg.get("content", "").strip()
            
            # NEVER return raw English internal reasoning text to user!
            # Only use content. If content is empty, check if explicit section tags exist in reasoning
            if not content and "reasoning_content" in msg:
                rc = msg["reasoning_content"]
                for marker in ["===BAGIAN_1_", "===TAHAP_1_"]:
                    idx = rc.find(marker)
                    if idx != -1:
                        content = rc[idx:].strip()
                        break
            
            usage = data.get("usage", {})
            token_usage = {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
            return content.strip(), token_usage
    except urllib.error.HTTPError as he:
        err_msg = he.read().decode("utf-8", errors="ignore")
        logger.error(f"OpenCode API HTTP {he.code}: {err_msg}")
        raise RuntimeError(f"OpenCode API error ({he.code}): {err_msg}")
    except Exception as e:
        logger.error(f"OpenCode API call failed: {e}")
        raise

def call_opencode_image_generation(
    prompt: str,
    model: str = "openai/gpt-image-2",
    size: str = "1024x1024",
    timeout: int = 60
) -> bytes | None:
    """
    Generates image using OpenCode Zen API with model openai/gpt-image-2.
    Returns raw image bytes if successful, or None on error/unavailable.
    """
    import base64
    api_key = get_opencode_key()
    base_url = os.environ.get("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1").rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)"
    }

    # Attempt 1: Standard images/generations endpoint
    body_img = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size
    }
    try:
        req = urllib.request.Request(
            f"{base_url}/images/generations",
            data=json.dumps(body_img).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            if items:
                first = items[0]
                if "b64_json" in first:
                    return base64.b64decode(first["b64_json"])
                if "url" in first:
                    with urllib.request.urlopen(first["url"], timeout=timeout) as u_resp:
                        return u_resp.read()
    except Exception as e:
        logger.debug(f"[OpenCode Image Gen] images/generations failed: {e}")

    # Attempt 2: Chat completions with image generation prompt
    body_chat = {
        "model": model,
        "messages": [{"role": "user", "content": f"Generate image: {prompt}"}],
        "max_tokens": 1024
    }
    try:
        req2 = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(body_chat).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req2, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data.get("choices", [{}])[0].get("message", {})
            content = msg.get("content", "")
            if content and "data:image" in content:
                b64 = content.split("data:image", 1)[1].split(",", 1)[1].split()[0]
                return base64.b64decode(b64)
    except Exception as e:
        logger.debug(f"[OpenCode Image Gen] chat/completions failed: {e}")

    return None

