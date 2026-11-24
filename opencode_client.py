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
    base_url = os.environ.get("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/go/v1").rstrip("/")
    if base_url.endswith("/zen/v1"):
        base_url = "https://opencode.ai/zen/go/v1"
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)",
        "x-opencode-session": "hermes-default-session"
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
    model: str = "gpt-image-2.5-sunburst",
    size: str = "1024x1024",
    timeout: int = 90
) -> bytes | None:
    """
    Generates image using OpenCode Inference API (OpenAI / XAI provider).
    Primary model: gpt-image-2.5-sunburst (OpenAI)
    Fallback model: grok-imagine-image-2.0 (xAI)
    Returns raw image bytes if successful, or None on failure.
    """
    import base64
    api_key = get_opencode_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)"
    }

    # Normalize model name
    eff_model = model.replace("openai/", "").replace("xai/", "")
    if eff_model in ("gpt-image-2", "gpt-image-2.5", "gpt-image-2.5-sunburst"):
        eff_model = "gpt-image-2.5-sunburst"

    # Attempt 1: OpenAI inference endpoint
    url_openai = "https://opencode.ai/inference/openai/v1/images/generations"
    body_img = {
        "model": eff_model if eff_model.startswith("gpt-") else "gpt-image-2.5-sunburst",
        "prompt": prompt,
        "n": 1,
        "size": size
    }
    try:
        req = urllib.request.Request(
            url_openai,
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
        logger.warning(f"[OpenCode Image Gen] OpenAI inference failed: {e}")

    # Attempt 2: xAI Grok inference endpoint
    url_xai = "https://opencode.ai/inference/xai/v1/images/generations"
    body_xai = {
        "model": "grok-imagine-image-2.0",
        "prompt": prompt,
        "n": 1,
        "size": size
    }
    try:
        req_xai = urllib.request.Request(
            url_xai,
            data=json.dumps(body_xai).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req_xai, timeout=timeout) as resp:
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
        logger.warning(f"[OpenCode Image Gen] xAI Grok inference failed: {e}")

    return None

def call_opencode_video_generation(
    prompt: str,
    model: str = "grok-imagine-video-1.5-lite",
    duration: int = 5,
    max_wait_seconds: int = 120,
    poll_interval: int = 3
) -> tuple[bytes | None, str | None]:
    """
    Generates video using OpenCode Inference API (xAI grok-imagine-video-1.5-lite / grok-imagine-video-1.5).
    Submits generation job, polls until completion, and downloads final .mp4.
    Returns (video_bytes, video_url).
    """
    import time
    api_key = get_opencode_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)"
    }

    url_submit = "https://opencode.ai/inference/xai/v1/videos/generations"
    body = {
        "model": model,
        "prompt": prompt,
        "duration": duration
    }

    try:
        req = urllib.request.Request(
            url_submit,
            data=json.dumps(body).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rid = data.get("request_id")
            if not rid:
                logger.error("[OpenCode Video Gen] No request_id returned")
                return None, None
            logger.info(f"[OpenCode Video Gen] Job submitted: {rid}")
    except Exception as e:
        logger.error(f"[OpenCode Video Gen] Submit failed: {e}")
        return None, None

    # Poll status
    poll_url = f"https://opencode.ai/inference/xai/v1/videos/{rid}"
    poll_headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PegawaiAI/2.0 (Windows NT 10.0; Win64; x64)"
    }

    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        time.sleep(poll_interval)
        try:
            req_poll = urllib.request.Request(poll_url, headers=poll_headers)
            with urllib.request.urlopen(req_poll, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
                st = res.get("status")
                logger.info(f"[OpenCode Video Gen] Polling {rid}: status={st}, progress={res.get('progress')}%")
                if st == "done":
                    v_url = res.get("video", {}).get("url")
                    if v_url:
                        # Download .mp4
                        req_dl = urllib.request.Request(v_url, headers={"User-Agent": "PegawaiAI/2.0"})
                        with urllib.request.urlopen(req_dl, timeout=60) as dl_resp:
                            v_bytes = dl_resp.read()
                            return v_bytes, v_url
                    return None, v_url
                if st in ("failed", "error"):
                    logger.error(f"[OpenCode Video Gen] Job {rid} failed: {res}")
                    return None, None
        except Exception as e:
            logger.warning(f"[OpenCode Video Gen] Polling error: {e}")

    logger.warning(f"[OpenCode Video Gen] Timed out waiting for job {rid}")
    return None, None

