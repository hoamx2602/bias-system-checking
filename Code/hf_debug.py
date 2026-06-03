import json
import sys
import traceback

from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

import download_model
import config


def main() -> int:
    token = download_model.get_hf_token()
    print(f"Token present: {bool(token)}")
    if token:
        print(f"Token preview: {token[:6]}...{token[-6:]} (len={len(token)})")

    api = HfApi()

    try:
        me = api.whoami(token=token)
        print("whoami: ", json.dumps(me))
    except HfHubHTTPError as e:
        print("whoami HTTP error:")
        try:
            status = e.response.status_code if e.response is not None else None
            text = e.response.text if e.response is not None else None
        except Exception:
            status = None
            text = None
        print(json.dumps({
            "type": type(e).__name__,
            "status": status,
            "text": text,
        }))
        return 1
    except Exception as e:
        print("whoami generic error:")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        return 1

    try:
        info = api.model_info(repo_id=config.GENERATIVE_MODEL, token=token)
        print("model_info ok: ", info.modelId)
        return 0
    except HfHubHTTPError as e:
        print("model_info HTTP error:")
        try:
            status = e.response.status_code if e.response is not None else None
            text = e.response.text if e.response is not None else None
        except Exception:
            status = None
            text = None
        print(json.dumps({
            "type": type(e).__name__,
            "status": status,
            "text": text,
        }))
        return 2
    except Exception as e:
        print("model_info generic error:")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())


