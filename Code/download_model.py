import os
import config  # loads .env and configures HF environment variables

from huggingface_hub import snapshot_download, HfApi
from huggingface_hub.utils import HfHubHTTPError


def get_hf_token():
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    return token.strip().strip('"').strip("'") if token else None


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
            "and set HF_TOKEN in your .env file."
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
        print("Please set HF_TOKEN in your .env file.")
        return

    try:
        # Validate token and model access upfront for clearer errors
        validate_token_and_access(token=token, repo_id=retrieval_model)
        validate_token_and_access(token=token, repo_id=gen_model)
        validate_token_and_access(token=token, repo_id=classifier_model)

        cache_root = os.environ["HF_HOME"]

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
        err = str(e)
        print(f"\n--- An error occurred during download: {e} ---")
        if "403" in err or "gated" in err or "not in the authorized list" in err:
            print("\nACCESS DENIED (403): This is a gated model requiring explicit license acceptance.")
            print("Steps to fix:")
            print("  1. Visit the model page on huggingface.co and click 'Acknowledge license'")
            print("  2. Make sure your HF_TOKEN in .env belongs to the same account")
            print("  3. Re-run this script")
        elif "401" in err:
            print("\nAUTHENTICATION FAILED (401): Your HF_TOKEN may be invalid or expired.")
            print("Generate a new READ token at https://huggingface.co/settings/tokens and update .env")
        else:
            print("\nPlease check your internet connection and try running this script again.")

if __name__ == "__main__":
    main() 