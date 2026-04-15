import base64
import os
import sys
from pathlib import Path


def ensure_firebase_credentials_file() -> None:
    """Create a local Firebase credentials file from environment variables."""
    credentials_env = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if credentials_env and Path(credentials_env).exists():
        return

    raw_json = os.environ.get("FIREBASE_CREDENTIALS_JSON_RAW")
    b64_json = os.environ.get("FIREBASE_CREDENTIALS_JSON_BASE64")
    if not raw_json and not b64_json:
        return

    target_path = Path("serviceAccountKey.json")
    if raw_json:
        target_path.write_text(raw_json, encoding="utf-8")
    else:
        cleaned = "".join(b64_json.split())
        if len(cleaned) % 4 != 0:
            cleaned += "=" * (4 - len(cleaned) % 4)
        try:
            decoded = base64.b64decode(cleaned)
        except Exception:
            print("ERROR: FIREBASE_CREDENTIALS_JSON_BASE64 is not valid base64.", file=sys.stderr)
            raise
        target_path.write_bytes(decoded)

    os.environ["FIREBASE_CREDENTIALS_JSON"] = str(target_path.resolve())
    print(f"Wrote Firebase credentials to {target_path.resolve()}")


if __name__ == "__main__":
    ensure_firebase_credentials_file()
    port = os.environ.get("PORT", "8000")
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api_server_enhanced:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
        ],
    )
