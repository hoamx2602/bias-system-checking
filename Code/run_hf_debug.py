"""Entry point: diagnoses Hugging Face token / model-access issues (see src/scripts/hf_debug.py)."""
import sys
from src.scripts.hf_debug import main

if __name__ == '__main__':
    sys.exit(main())
