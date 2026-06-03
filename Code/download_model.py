from huggingface_hub import snapshot_download, HfApi
from huggingface_hub.utils import HfHubHTTPError
import config
import os
import configparser

def get_hf_token():
    """Reads the Hugging Face token from config.ini"""
    # Support inline comments like: token = hf_xxx  # my token
    parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    parser.read('config.ini')
    token = parser.get('huggingface', 'token', fallback=None)
    if token:
        token = token.strip().strip('"').strip("'")
    # Fallback to environment variables if not present in config.ini
    if not token or "YOUR_HUGGING_FACE_TOKEN_HERE" in token:
        token = os.environ.get("HUGGING_FACE_HUB_TOKEN") or os.environ.get("HF_TOKEN")
        if token:
            token = token.strip().strip('"').strip("'")
    return token if token else None


def validate_token_and_access(token: str, repo_id: str) -> None:
    """Validate token correctness and access to the target repo.

    Raises a clear exception with guidance if invalid or access denied.
    """
    api = HfApi()
    try:
        # Validate token by calling whoami
        api.whoami(token=token)
    except HfHubHTTPError as e:
        # Invalid token → 401
        raise RuntimeError(
            "Your Hugging Face token appears invalid (401). "
            "Please create a new READ token at https://huggingface.co/settings/tokens "
            "and update it in config.ini or set HUGGING_FACE_HUB_TOKEN."
        ) from e
    except Exception as e:
        raise RuntimeError("Failed to validate Hugging Face token. Check your network and try again.") from e

    try:
        # Check access to the specific model
        api.model_info(repo_id=repo_id, token=token)
    except HfHubHTTPError as e:
        status = getattr(e, "response", None).status_code if getattr(e, "response", None) else None
        if status == 401:
            raise RuntimeError(
                "Authentication failed with 401 for the model. Your token may be invalid or expired."
            ) from e
        if status == 403:
            raise RuntimeError(
                "Access denied (403). If the model is gated, please accept the model license "
                "on its Hugging Face page while logged in, then try again."
            ) from e
        raise

def main():
    """
    Downloads the generative model from the Hugging Face Hub to the local cache.
    This is a separate, dedicated script to make the download process more robust 
    against network interruptions. Run this script before starting the main app.
    """
    gen_model = config.GENERATIVE_MODEL
    retrieval_model = config.RETRIEVAL_MODEL
    classifier_model = config.CLASSIFIER_MODEL
    
    # Set HF_HUB_ENABLE_HF_TRANSFER for faster downloads if available.
    # This uses a more efficient library for downloading large files.
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    
    print("--- Preparing downloads ---")
    print(f"Retrieval model: {retrieval_model}")
    print(f"Generative model: {gen_model}")
    print(f"Classifier base model: {classifier_model}")
    print("These may take a long time depending on your internet connection.")
    
    token = get_hf_token()
    if not token:
        print("\n--- ERROR: Hugging Face token not found. ---")
        print("Add your READ token to 'config.ini' under [huggingface] token = ...")
        print("Or set the environment variable HUGGING_FACE_HUB_TOKEN or HF_TOKEN.")
        return

    try:
        # Validate token and model access upfront for clearer errors
        validate_token_and_access(token=token, repo_id=retrieval_model)
        validate_token_and_access(token=token, repo_id=gen_model)
        validate_token_and_access(token=token, repo_id=classifier_model)


        # Set the token as an environment variable for compatibility
        os.environ["HUGGING_FACE_HUB_TOKEN"] = token

        # Use a workspace-local cache on the current drive to avoid Windows symlink privilege issues
        cache_root = os.path.join(os.getcwd(), "@.hf_cache")
        os.makedirs(cache_root, exist_ok=True)
        os.environ["HF_HOME"] = cache_root
        os.environ["HUGGINGFACE_HUB_CACHE"] = cache_root
        # Avoid symlink/hardlink operations on Windows; copy files instead
        os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
        os.environ["HF_HUB_DISABLE_HARDLINKS"] = "1"
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        # Limit downloads to essential files only
        retrieval_allow = [
            "config.json",
            "config_sentence_transformers.json",
            "modules.json",
            "pytorch_model.bin",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "*.safetensors",
        ]
        gen_allow = [
            "config.json",
            "generation_config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "vocab.txt",
            "*.safetensors",
        ]

        # snapshot_download with an explicit cache_dir and limited files (avoids large ONNX assets and symlink issues)
        snapshot_download(
            repo_id=retrieval_model,
            token=token,
            cache_dir=cache_root,
            allow_patterns=retrieval_allow,
        )
        print(f"\n--- Retrieval model '{retrieval_model}' downloaded successfully! ---")

        # Download the generative model
        snapshot_download(
            repo_id=gen_model,
            token=token,
            cache_dir=cache_root,
            allow_patterns=gen_allow,
        )
        print(f"\n--- Generative model '{gen_model}' downloaded successfully! ---")

        # Download the classifier base model
        print(f"\n--- Downloading classifier model '{classifier_model}' ---")
        snapshot_download(
            repo_id=classifier_model,
            token=token,
            cache_dir=cache_root,
        )
        print(f"--- Classifier model '{classifier_model}' downloaded successfully! ---")
        
        print("\nYou can now start the main application by running:")
        print("python app.py")
        
    except Exception as e:
        print(f"\n--- An error occurred during download: {e} ---")

        print("\nPlease check your internet connection and try running this script again.")
        print("If the problem persists, you may have a firewall, VPN, or proxy blocking the connection to huggingface.co.")

if __name__ == "__main__":
    main() 