# Codebase Walkthrough (Fully Annotated, Line-by-Line)

This document explains every Python file in the repository. For each file:
- A brief starting explanation (overview)
- The complete code with per-line inline explanations appended as comments

Use this as a definitive reference for understanding the flow and intent behind every line.

---

## app.py

Overview: Flask web application that loads the AI bias analysis pipeline once, exposes routes for UI, evaluation, and analysis, and serves static assets.

```1:98:app.py
from flask import Flask, request, jsonify, render_template, send_from_directory  # Import Flask core APIs for HTTP handling, templating, and static file serving
import os  # OS utilities for filesystem checks
from models import get_analysis_pipeline  # Import factory to initialize the RAG analysis pipeline (singleton)
import config  # Centralized configuration module

# --- Flask App Initialization ---  # Section: App creation and initialization
app = Flask(__name__)  # Create Flask app instance

# --- Pre-load the full analysis pipeline ---  # Section: Eagerly initialize heavy models once at startup
# This ensures the models are loaded into memory only once when the app starts.  # Rationale: Avoid per-request cold starts
print("Starting the application and loading AI models... Please wait.")  # Log startup
try:  # Attempt to build pipeline
    analysis_pipeline = get_analysis_pipeline()  # Build or reuse singleton pipeline
    print("Models loaded successfully. Application is ready.")  # Success log
except Exception as e:  # If pipeline initialization fails
    print(f"FATAL: Could not initialize the AI pipeline. Error: {e}")  # Log fatal error (non-blocking for app boot)
    analysis_pipeline = None  # Mark pipeline unavailable so routes can report errors

# --- Static File Serving ---  # Section: Serve generated static assets (e.g., knowledge graph)
# Route to serve the generated knowledge graph image  # Explain purpose
@app.route('/static/<path:filename>')  # Dynamic static route to read from ./static
def serve_static(filename):  # Handler receives a relative file path
    return send_from_directory('static', filename)  # Serve file from 'static' directory

# --- Main Application Routes ---  # Section: UI and API endpoints
@app.route('/')  # Home page route
def index():  # Handler for index page
    """Renders the main user interface."""  # Docstring for clarity
    # Pass the path to the knowledge graph image to the template  # Template param explanation
    graph_image_path = config.KNOWLEDGE_GRAPH_IMAGE_PATH if os.path.exists(config.KNOWLEDGE_GRAPH_IMAGE_PATH) else None  # Include image path only if generated
    return render_template('index.html', knowledge_graph_image=graph_image_path)  # Render template with optional image

@app.route('/evaluation')  # Page to run batch evaluation
def evaluation():  # Handler for evaluation page
    """Renders the evaluation page."""  # Docstring
    return render_template('evaluation.html', questions=config.EVALUATION_QUESTIONS)  # Provide predefined questions from config

@app.route('/run_evaluation', methods=['POST'])  # API to run batch evaluation across preset questions
def run_evaluation():  # Handler for evaluation run
    """Runs the full evaluation suite."""  # Docstring
    if not analysis_pipeline:  # Guard: pipeline failed to initialize at startup
        return jsonify({  # Respond with error JSON
            "error": "The AI analysis pipeline is not available."
        }), 500  # Internal server error status
    
    results = []  # Collect per-question results
    for question in config.EVALUATION_QUESTIONS:  # Iterate predefined evaluation prompts
        try:  # Try to analyze each question
            result = analysis_pipeline.analyze(question)  # Run RAG pipeline
            results.append({  # Append structured result for UI consumption
                "question": question,
                "answer": result['answer'],
                "source_contexts": result['source_contexts'],
                "bias_type": result['bias_type']
            })
        except Exception as e:  # If analysis fails for one question, continue others
            results.append({  # Report per-question error instead of failing entire batch
                "question": question,
                "error": str(e)
            })
    return jsonify({"results": results})  # Return array of results/errors

@app.route('/analyze', methods=['POST'])  # Primary API endpoint for ad-hoc analysis
def analyze():  # Handler for single analysis request
    """
    Handles the analysis request from the user.
    This endpoint implements the core logic as per the flowchart.
    """  # High-level behavior
    if not analysis_pipeline:  # Ensure pipeline is ready
        return jsonify({  # Report unavailability to client
            "error": "The AI analysis pipeline is not available. Please check the server logs."
        }), 500  # Error status

    try:  # Wrap processing for error safety
        data = request.get_json()  # Parse JSON body
        user_question = data.get('question')  # Extract question string

        if not user_question:  # Validate required field
            return jsonify({"error": "No question provided."}), 400  # Bad request

        # Delegate the entire analysis to our pipeline  # Separation of concerns
        result = analysis_pipeline.analyze(user_question)  # Execute pipeline

        return jsonify(result)  # Return full pipeline response

    except Exception as e:  # Catch unexpected errors
        print(f"An error occurred during analysis: {e}")  # Log for debugging
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500  # Generic error

# --- Main Execution ---  # Section: dev/prod entrypoint
if __name__ == '__main__':  # Only run the server if executed directly
    # Make sure the static directory exists  # Ensure path for served assets
    if not os.path.exists('static'):  # Check for directory
        os.makedirs('static')  # Create if missing
    
    # The debug=False is important for production and to avoid loading models twice.  # Guidance for usage
    # For development, you might enable it, but be aware of the double-loading.  # Flask debug reload caveat
    app.run(host='0.0.0.0', port=5001, debug=False)  # Start HTTP server on port 5001, bound to all interfaces
```

---

## config.py

Overview: Central configuration for paths, model IDs, thresholds, hyperparameters, prompt template, and evaluation questions.

```1:70:config.py
import torch  # Used to detect CUDA availability for GPU usage

# --- File Paths ---  # Central locations for artifacts and data
DATA_DIR = "dataset"  # Directory containing JSON data files
VECTOR_STORE_PATH = "bias_vector_store.pkl"  # Serialized vector store path
TRAINED_MODEL_DIR = "models/bias_classifier"  # Output directory for trained classifier
RESULTS_DIR = "results"  # Transformers Trainer output directory
LOGS_DIR = "logs"  # Logging directory for training
EVALUATION_RESULTS_DIR = "evaluation_results"  # Where evaluation images/metrics are saved
KNOWLEDGE_GRAPH_IMAGE_PATH = "static/knowledge_graph.png"  # Output path for graph visualization

# --- Model Configuration ---  # Retrieval and generation model choices
# Model for semantic search and context retrieval  # Sentence-transformers model name
RETRIEVAL_MODEL = "sentence-transformers/all-mpnet-base-v2"  # High-quality embedding model
# Generative model for answering questions based on context  # HF Causal LM ID
GENERATIVE_MODEL = "google/gemma-3-1b-it"  # Instruction-tuned Gemma 3 (chat template)
# Optional: A classifier model for a supplemental bias score (can be trained via train.py)  # HF classification model
CLASSIFIER_MODEL = "distilbert-base-uncased"  # Lightweight baseline classifier

# --- Vector Store & Knowledge Graph ---  # Graph generation parameters
SIMILARITY_THRESHOLD = 0.65  # For connecting similar scenarios in the graph  # Cosine similarity cutoff
GRAPH_NODE_COUNT_LIMIT = 50   # Max nodes for visualization to keep it readable  # Subgraph viz cap

# --- Training Hyperparameters (for train.py) ---  # Training defaults
USE_PRETRAINED_CLASSIFIER = True  # Whether to start from pretrained weights
TRAIN_SAMPLE_RATIO = 1.0  # Use 100% of data for training  # Downsample knob
TEST_SPLIT_SIZE = 0.2  # Validation split fraction
TRAIN_EPOCHS = 3  # Number of training epochs
TRAIN_BATCH_SIZE = 8  # Per-device train batch size
EVAL_BATCH_SIZE = 8  # Per-device eval batch size
WARMUP_STEPS = 500  # Linear warmup steps
WEIGHT_DECAY = 0.01  # AdamW weight decay
LOGGING_STEPS = 50  # Logging frequency
LEARNING_RATE = 5e-5  # Optimizer learning rate

# --- Application Settings ---  # Runtime settings
# Set to True if a GPU is available, False otherwise  # Auto-detect device
USE_CUDA = torch.cuda.is_available()  # Boolean flag for CUDA device availability
PROMPT_TEMPLATE = """
You are an AI Bias and Ethics Analyst. Your task is to provide a clear, neutral, and informative answer to the user's question based *only* on the context provided.

**Instructions:**
1.  Carefully read the user's question and all of the provided context documents.
2.  Synthesize the information from the context to formulate a comprehensive answer.
3.  Do not use any information outside of the provided context.
4.  Directly answer the user's question. Do not just summarize the context.
5.  If the context does not contain enough information to answer the question, state that you cannot provide a definitive answer based on the available information.

**Context Document(s):**
---
{context}
---

**User's Question:**
{question}

**Analyst's Answer:**
"""  # Template filled with retrieved context and the question

# --- Evaluation Settings ---  # Default evaluation prompts for UI and batch route
EVALUATION_QUESTIONS = [  # List of representative questions across bias types
    "What are the risks of overlooking contributions from women in tech?",  # Gender bias
    "How can stereotypes about age affect hiring decisions for older candidates?",  # Age bias
    "Why is it problematic to assume someone's capabilities based on their accent?",  # Accent bias
    "Describe a scenario where social class bias might appear in a professional setting.",  # Class bias
    "How might an AI recruitment tool develop a bias against candidates from non-traditional educational backgrounds?",  # Education bias
    "What kind of intersectional bias might a disabled woman from a racial minority face in the workplace?",  # Intersectional
    "Explain how confirmation bias can affect a manager's performance review of an employee.",  # Cognitive bias
    "In what ways can regional stereotypes lead to unfair treatment in a national company?"  # Regional bias
]  # End evaluation questions
```

---

## create_static_assets.py

Overview: Setup helper to ensure `static/` exists and to create a placeholder system diagram image; intended as a bootstrap utility.

```1:31:create_static_assets.py
import os  # Filesystem operations
import base64  # (Unused here) Could be used for decoding embedded images
from PIL import Image  # Pillow for image creation/manipulation
import io  # (Unused here) For in-memory streams when needed
import shutil  # (Unused here) For file/directory operations

def create_static_directory():  # Ensure static directory exists
    """Create static directory if it doesn't exist"""  # Docstring
    if not os.path.exists("static"):  # Check existence
        os.makedirs("static")  # Create directory tree
        print("Created static directory")  # Log creation
    else:  # Directory already present
        print("Static directory already exists")  # Log status

def save_system_diagram():  # Create a placeholder diagram image
    """Save the system diagram image to static/bias_design_flow.png"""  # Docstring
    # Create an empty image as placeholder (in a real scenario, you would use the actual diagram)  # Note on placeholder
    # In a real implementation, you would save the provided system diagram here  # Instruction for production
    # For now, we'll create a placeholder image  # Clarification
    placeholder_image = Image.new('RGB', (800, 400), color='white')  # Generate white image 800x400
    
    # Save the image  # Persist to disk
    placeholder_image.save('static/bias_design_flow.png')  # Write to static path
    
    print("Created system diagram placeholder at static/bias_design_flow.png")  # Log success
    print("Note: In a real implementation, you should replace this with the actual system diagram.")  # Reminder

if __name__ == "__main__":  # CLI entrypoint
    create_static_directory()  # Ensure static directory
    save_system_diagram()  # Generate placeholder image
    print("Static assets created successfully!")  # Final log
```

---

## download_model.py

Overview: Robust downloader to pre-cache the large generative model from Hugging Face using an access token from `config.ini`.

```1:58:download_model.py
from huggingface_hub import snapshot_download  # HF utility to download entire model repos reliably
import config  # Access configured model repo ID
import os  # Environment and filesystem
import configparser  # Read token from config.ini

def get_hf_token():  # Load HF token from config file
    """Reads the Hugging Face token from config.ini"""  # Docstring
    parser = configparser.ConfigParser()  # INI parser
    parser.read('config.ini')  # Read config file
    token = parser.get('huggingface', 'token', fallback=None)  # Get token value or None
    if not token or "YOUR_HUGGING_FACE_TOKEN_HERE" in token:  # Validate presence and not placeholder
        return None  # Indicate missing/invalid token
    return token  # Return token string

def main():  # Entrypoint for model snapshot download
    """
    Downloads the generative model from the Hugging Face Hub to the local cache.
    This is a separate, dedicated script to make the download process more robust 
    against network interruptions. Run this script before starting the main app.
    """  # Purpose
    model_name = config.GENERATIVE_MODEL  # Repo ID to download
    
    # Set HF_HUB_ENABLE_HF_TRANSFER for faster downloads if available.  # Performance tweak
    # This uses a more efficient library for downloading large files.  # Explanation
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"  # Enable accelerated transfer
    
    print(f"--- Starting download for model: {model_name} ---")  # Announce start
    print("This is a large model and may take a long time depending on your internet connection.")  # Warning
    print("The model will be saved to your Hugging Face cache directory.")  # Cache info
    print("Please ensure you have a stable internet connection.")  # Advice
    
    token = get_hf_token()  # Retrieve token
    if not token:  # Check availability
        print("\n--- ERROR: Hugging Face token not found in config.ini ---")  # Error message
        print("Please add your token to the 'config.ini' file to continue.")  # Instruction
        return  # Abort

    try:  # Protected download block
        # Set the token as an environment variable for compatibility  # Downstream libs read env var
        os.environ["HUGGING_FACE_HUB_TOKEN"] = token  # Export token

        # snapshot_download is the recommended way to download an entire model repository.  # Method
        # It is more resilient to interruptions than the automatic download from .from_pretrained()  # Benefit
        snapshot_download(
            repo_id=model_name,  # Which repo to download
            resume_download=True, # Attempt to resume if interrupted  # Resilience
        )
        print(f"\n--- Model '{model_name}' downloaded successfully! ---")  # Success
        print("\nYou can now start the main application by running:")  # Next step
        print("python app.py")  # Command
        
    except Exception as e:  # Catch and report issues
        print(f"\n--- An error occurred during download: {e} ---")  # Error details
        print("\nPlease check your internet connection and try running this script again.")  # Troubleshooting
        print("If the problem persists, you may have a firewall, VPN, or proxy blocking the connection to huggingface.co.")  # More tips

if __name__ == "__main__":  # Script entrypoint
    main()  # Invoke downloader
```

---

## models.py

Overview: Implements the RAG pipeline by combining retrieval from `BiasVectorStore` and generation using a Hugging Face causal LM; exposes a singleton factory `get_analysis_pipeline` for reuse.

```1:160:models.py
import os  # For environment variable management
import torch  # Tensor library and device utilities
from transformers import AutoTokenizer, AutoModelForCausalLM  # HF tokenizer and causal LM loader
from vector_store import get_vector_store  # Vector store builder/loader
import config  # Configuration values
import configparser  # To read HF token from config.ini

def get_hf_token():  # Helper to obtain token
    """Reads the Hugging Face token from config.ini"""  # Docstring
    parser = configparser.ConfigParser()  # Create parser
    parser.read('config.ini')  # Load INI file
    token = parser.get('huggingface', 'token', fallback=None)  # Get token or None
    if not token or "YOUR_HUGGING_FACE_TOKEN_HERE" in token:  # Validate token content
        return None  # Missing or placeholder
    return token  # Return token string

class BiasAnalysisPipeline:  # Main pipeline class encapsulating RAG
    """
    A pipeline that integrates the vector store for retrieval and a generative
    model for answering questions based on the retrieved context.
    """  # High-level description
    def __init__(self, vector_store):  # Initialize with a vector store instance
        print("Initializing Bias Analysis Pipeline...")  # Log init
        self.vector_store = vector_store  # Save store reference
        
        # Determine the device to use  # Choose CPU/GPU
        self.device = "cuda" if config.USE_CUDA else "cpu"  # Respect config auto-detect
        print(f"Using device: {self.device}")  # Report chosen device

        # Get auth token and set it as an environment variable  # Required to access private models if needed
        auth_token = get_hf_token()  # Read token
        if not auth_token:  # Validation
            raise ValueError("Hugging Face token not found in config.ini. Please add it to continue.")  # Fail fast
        os.environ["HUGGING_FACE_HUB_TOKEN"] = auth_token  # Export token for HF libraries

        # Load the generative model and tokenizer  # HF model load
        print(f"Loading generative model: {config.GENERATIVE_MODEL}...")  # Log
        self.tokenizer = AutoTokenizer.from_pretrained(config.GENERATIVE_MODEL)  # Load tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(  # Load causal LM
            config.GENERATIVE_MODEL,
            torch_dtype=torch.float16, # Use float16 for memory efficiency  # Lower memory
            device_map="auto" # Automatically use GPU if available  # Device placement
        )

        # Set pad token if it's not set  # Ensure padding token is defined
        if self.tokenizer.pad_token is None:  # If tokenizer lacks pad token
            self.tokenizer.pad_token = self.tokenizer.eos_token  # Use EOS as pad

        self.model.eval() # Set model to evaluation mode  # Disable dropout etc.
        print("Generative model loaded successfully.")  # Log success

    def analyze(self, user_question):  # Main analysis entrypoint
        """
        Analyzes a user's question by retrieving context and generating an answer.
        This method implements the core RAG (Retrieval-Augmented Generation) flow.

        Args:
            user_question (str): The question provided by the user.

        Returns:
            dict: A dictionary containing the generated answer and the source context.
        """  # Contract
        print(f"Analyzing question: '{user_question}'")  # Trace input
        
        # --- Step 1: Retrieve Context ---  # Retrieval stage
        # Use the vector store to find the most relevant bias scenarios.  # Purpose
        # Retrieving the top 3 for a richer context.  # Depth of retrieval
        print("Step 1: Retrieving relevant context from vector store...")  # Trace
        retrieved_results = self.vector_store.search(user_question, top_k=3)  # Query embeddings
        
        if not retrieved_results:  # No results fallback
            print("No relevant context found.")  # Log
            return {
                "answer": "I could not find a relevant context in my knowledge base to answer your question. Please try rephrasing it.",  # Apology
                "source_contexts": ["No context found."],  # Empty context note
                "bias_type": "N/A"  # Unknown
            }  # Early return
            
        # Combine the text from the top results to form the context  # Build prompt context block
        source_contexts = [result['text'] for result in retrieved_results]  # Extract texts
        combined_context = "\n\n---\n\n".join(source_contexts)  # Separate with markers

        # The primary bias type is from the most relevant document  # Heuristic label
        bias_type = retrieved_results[0]['bias_type']  # Take top result's type
        print(f"Found context from bias types: {[r['bias_type'] for r in retrieved_results]}")  # Log types

        # --- Step 2: Construct Prompt ---  # Prompt engineering
        # Create a detailed prompt using the template from the config file  # Template usage
        print("Step 2: Constructing prompt for the generative model...")  # Trace
        # For Gemma 3, build chat messages and use apply_chat_template
        user_prompt = config.PROMPT_TEMPLATE.format(context=combined_context, question=user_question)
        messages = [[
            {"role": "system", "content": [{"type": "text", "text": "You are an AI Bias and Ethics Analyst. Follow the instructions and base your answers only on the provided context."}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
        ]]

        # --- Step 3: Generate Answer ---  # Decoding stage
        # Use the generative model to synthesize an answer  # Purpose
        print("Step 3: Generating answer...")  # Trace
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        
        with torch.no_grad():  # Disable gradients for inference
            outputs = self.model.generate(  # Generate text continuation
                **inputs,
                max_length=300,  # Cap total tokens
                temperature=0.7,  # Sampling temperature
                top_p=0.95,  # Nucleus sampling
                length_penalty=1.5,  # Encourage shorter outputs
                num_beams=5,  # Beam search beams
                early_stopping=True,  # Stop when beams converge
                repetition_penalty=1.2,  # Penalize repetition
                no_repeat_ngram_size=3  # Avoid repeating 3-grams
            )
        
        input_len = inputs["input_ids"].shape[1]
        generated_ids = outputs[0]
        generated_text = self.tokenizer.decode(generated_ids[input_len:], skip_special_tokens=True)

        print("Answer generated successfully.")  # Trace

        return {  # Structured response
            "answer": generated_text,  # Generated answer
            "source_contexts": source_contexts,  # Context snippets used
            "bias_type": bias_type  # Primary bias label
        }  # End return

# --- Singleton instance ---  # Global cached instance for reuse
# This ensures that the models and vector store are loaded only once.  # Rationale
_pipeline = None  # Module-level cache

def get_analysis_pipeline(force_rebuild_store=False):  # Factory to get or build pipeline
    """
    Initializes and returns a singleton instance of the BiasAnalysisPipeline.
    """  # Docstring
    global _pipeline  # Modify module-global
    if _pipeline is None:  # Build on first call
        # First, get the vector store (build it if it doesn't exist)  # Ensure store ready
        vector_store = get_vector_store(force_rebuild=force_rebuild_store)  # Load/build store
        
        # Then, initialize the pipeline with the store  # Compose pipeline
        _pipeline = BiasAnalysisPipeline(vector_store=vector_store)  # Construct pipeline
        
    return _pipeline  # Return cached instance

if __name__ == '__main__':  # Standalone test run
    # Example usage of the pipeline  # Context
    print("--- Running standalone example ---")  # Banner
    pipeline = get_analysis_pipeline()  # Get pipeline
    
    # Example question  # Test input
    test_question = "What are the risks of overlooking contributions from women in tech?"  # Example prompt
    
    # Analyze the question  # Execute
    result = pipeline.analyze(test_question)  # Get result
    
    # Print the results  # Display
    print("\n--- Analysis Result ---")  # Header
    print(f"Question: {test_question}")  # Echo question
    print(f"\nAnswer: {result['answer']}")  # Show answer
    print(f"\nSource Contexts: {result['source_contexts']}")  # Show contexts
    print(f"Detected Bias Type: {result['bias_type']}")  # Show bias type
    print("-------------------------")  # Footer
```

---

## preprocess_data.py

Overview: Builds knowledge assets: loads dataset JSON files, constructs vector embeddings and a knowledge graph, saves the store, and can report dataset statistics.

```1:142:preprocess_data.py
"""
Preprocess the bias dataset and create vector embeddings  # Module overview

This script loads the bias dataset, creates embeddings using SentenceTransformers,  # Purpose
and saves the vector store for faster loading in the main application.  # Outcome
"""  # End module docstring

import os  # Filesystem utilities
import json  # JSON parsing
import time  # Timing utilities
import argparse  # CLI argument parsing
from tqdm import tqdm  # (Imported but not currently used) for progress bars
import config  # Config
from vector_store import BiasVectorStore  # Core vector store class

def build_knowledge_assets():  # Main function to build assets
    """
    Builds all necessary knowledge assets, including the vector store  # Summary
    and the knowledge graph visualization.  # Includes graph image
    """  # End docstring
    print("--- Starting Knowledge Asset Building Process ---")  # Banner
    start_time = time.time()  # Start timer

    # --- 1. Check if assets already exist ---  # Idempotency check
    if os.path.exists(config.VECTOR_STORE_PATH):  # If store exists prompt
        try:
            response = input(f"Vector store already exists at '{config.VECTOR_STORE_PATH}'. Rebuild it? [y/N]: ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ("y", "yes"):
            print("Skipping rebuild. Using existing assets.")
            return  # Exit early

    print("Building new vector store from data...")  # Status
    
    # --- 2. Create and Populate Vector Store ---  # Build stage
    # Lazy import to avoid heavy deps unless rebuilding
    from vector_store import BiasVectorStore
    vector_store = BiasVectorStore()  # Instantiate store (loads embedding model)
    
    print(f"Loading data from '{config.DATA_DIR}' directory...")  # Status
    vector_store.load_data(config.DATA_DIR)  # Load dataset and encode entries
    
    # --- 3. Save Vector Store ---  # Persistence stage
    print(f"Saving vector store to '{config.VECTOR_STORE_PATH}'...")  # Status
    vector_store.save()  # Serialize to disk
    
    # --- 4. Generate and Save Knowledge Graph Visualization ---  # Graph stage
    print("Generating knowledge graph visualization...")  # Status
    if not os.path.exists("static"):  # Ensure static dir exists
        os.makedirs("static")  # Create static dir
    
    graph_path = vector_store.visualize_graph(save_path=config.KNOWLEDGE_GRAPH_IMAGE_PATH)  # Render graph to file
    print(f"Knowledge graph visualization saved to '{graph_path}'")  # Report path
    
    end_time = time.time()  # Stop timer
    print("\n--- Knowledge Asset Building Complete ---")  # Banner
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")  # Duration
    print(f"Processed {len(vector_store.vectors)} text items with embeddings.")  # Count embeddings
    print(f"Knowledge graph has {vector_store.graph.number_of_nodes()} nodes and {vector_store.graph.number_of_edges()} edges.")  # Graph stats
    print("-----------------------------------------")  # Footer

def analyze_dataset_stats(data_dir="dataset"):  # Utility to summarize dataset makeup
    """Analyze and print statistics about the dataset"""  # Docstring
    bias_types = {}  # Map of type -> stats
    total_scenarios = 0  # Global scenario count
    total_dialogues = 0  # Global dialogue count
    bias_level_counts = {0: 0, 10: 0, 30: 0, 50: 0, 70: 0, 100: 0}  # Histogram of bias levels
    
    print(f"Analyzing dataset statistics in {data_dir}...")  # Status
    
    for filename in os.listdir(data_dir):  # Iterate data files
        if filename.startswith("bias_data_for_type_") and filename.endswith(".json"):  # Filter expected files
            bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]  # Extract bias type key
            
            filepath = os.path.join(data_dir, filename)  # Build path
            with open(filepath, 'r', encoding='utf-8') as f:  # Open JSON
                data = json.load(f)  # Load array of items
                
                # Count scenarios in this type  # Stat
                scenarios_count = len(data)  # Num items
                total_scenarios += scenarios_count  # Accumulate
                
                dialogues_count = 0  # Per-type dialogue accumulator
                
                # Count dialogues and bias levels  # Iterate nested entries
                for item in data:  # For each scenario
                    dialogues_count += len(item["parameters"]["conversations"])  # Count versions per scenario
                    
                    for conversation in item["parameters"]["conversations"]:  # Iterate versions
                        version = conversation["version"]  # Read label string
                        
                        # Count bias levels  # Increment histogram based on label
                        if "No Bias (0%)" in version:
                            bias_level_counts[0] += 1
                        elif "Very Low Bias (10%)" in version:
                            bias_level_counts[10] += 1
                        elif "Low Bias (30%)" in version:
                            bias_level_counts[30] += 1
                        elif "Moderate Bias (50%)" in version:
                            bias_level_counts[50] += 1
                        elif "High Bias (70%)" in version:
                            bias_level_counts[70] += 1
                        elif "Extreme Bias (100%)" in version:
                            bias_level_counts[100] += 1
                
                total_dialogues += dialogues_count  # Accumulate dialogues
                
                # Store stats for this bias type  # Record per-type stats
                bias_types[bias_type] = {
                    "scenarios": scenarios_count,  # Number of scenarios in type
                    "dialogues": dialogues_count,  # Number of dialogues in type
                    "avg_dialogues_per_scenario": dialogues_count / scenarios_count if scenarios_count > 0 else 0  # Average
                }
    
    # Print statistics  # Output summary
    print("\nDataset Statistics:")  # Header
    print(f"Total Bias Types: {len(bias_types)}")  # Number of types
    print(f"Total Scenarios: {total_scenarios}")  # Total scenarios
    print(f"Total Dialogues: {total_dialogues}")  # Total dialogues
    print(f"Average Dialogues per Scenario: {total_dialogues / total_scenarios:.2f}")  # Average dialogues/scenario
    
    print("\nBias Level Distribution:")  # Header
    total_bias_examples = sum(bias_level_counts.values())  # Total versions
    for level, count in bias_level_counts.items():  # Iterate histogram
        percentage = (count / total_bias_examples) * 100 if total_bias_examples > 0 else 0  # Percentage
        print(f"  {level}% Bias: {count} examples ({percentage:.2f}%)")  # Print row
    
    print("\nBias Types:")  # Header
    for bias_type, stats in bias_types.items():  # Per-type
        print(f"  {bias_type}:")  # Type name
        print(f"    Scenarios: {stats['scenarios']}")  # Count scenarios
        print(f"    Dialogues: {stats['dialogues']}")  # Count dialogues
        print(f"    Avg Dialogues per Scenario: {stats['avg_dialogues_per_scenario']:.2f}")  # Average

if __name__ == "__main__":  # CLI entrypoint
    parser = argparse.ArgumentParser(  # Argument parser
        description="Build all knowledge assets (Vector Store, Graph Visualization) for the Bias Detection System."  # Help text
    )
    _ = parser.parse_args()  # No flags
    build_knowledge_assets()  # Execute with prompt
```

---

## train.py

Overview: Trains a regression head on `distilbert-base-uncased` to predict normalized bias levels from dialogue texts; includes data loading, model setup, training, evaluation, and saving.

```1:168:train.py
import os  # Filesystem
import json  # JSON parsing
import numpy as np  # Array utilities and sampling
import torch  # Tensors
from torch.utils.data import Dataset  # PyTorch dataset base class
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments  # HF training stack
from sklearn.model_selection import train_test_split  # Split utility
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score  # Regression metrics
import config  # Hyperparameters and paths

# --- Dataset Class ---  # Torch dataset for texts/labels
class BiasDataset(Dataset):  # Simple dataset
    def __init__(self, texts, labels, tokenizer, max_length=512):  # Constructor
        self.texts = texts  # Store texts list
        self.labels = labels  # Store labels list (floats)
        self.tokenizer = tokenizer  # HF tokenizer
        self.max_length = max_length  # Max sequence length
        
    def __len__(self):  # Dataset length
        return len(self.texts)  # Number of items
    
    def __getitem__(self, idx):  # Item accessor
        text = str(self.texts[idx])  # Get text
        inputs = self.tokenizer(  # Tokenize text
            text,
            padding="max_length",  # Pad to max length
            truncation=True,  # Truncate long texts
            max_length=self.max_length,  # Max tokens
            return_tensors="pt"  # Return PyTorch tensors
        )
        inputs = {k: v.squeeze(0) for k, v in inputs.items()}  # Remove batch dimension
        inputs["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)  # Add regression label
        return inputs  # Return model inputs

# --- Data Loading ---  # Aggregate across all JSON files
def load_bias_data(data_dir=config.DATA_DIR, sample_ratio=config.TRAIN_SAMPLE_RATIO):  # Loader
    """Load and preprocess data from all bias dataset files."""  # Docstring
    all_texts = []  # Collect texts
    all_labels = []  # Collect normalized labels
    
    print(f"Loading data from {data_dir}...")  # Status
    for filename in os.listdir(data_dir):  # Iterate files
        if filename.startswith("bias_data_for_type_") and filename.endswith(".json"):  # Filter
            filepath = os.path.join(data_dir, filename)  # Path
            with open(filepath, 'r', encoding='utf-8') as f:  # Open file
                data = json.load(f)  # Parse JSON
                
                for item in data:  # For each scenario
                    for conversation in item["parameters"]["conversations"]:  # Each version
                        version = conversation["version"]  # Version label
                        dialogues = conversation["dialogues"]  # List of strings
                        
                        # Simplified bias level parsing  # Extract percent from label
                        bias_percentage = int(version.split('(')[-1].replace('%', '').replace(')', ''))  # Parse percent
                        normalized_bias = bias_percentage / 100.0  # Scale to [0,1]
                        
                        text = " ".join(dialogues)  # Concatenate dialogues
                        all_texts.append(text)  # Append text
                        all_labels.append(normalized_bias)  # Append label
    
    if sample_ratio < 1.0:  # Optional subsampling
        print(f"Sampling {sample_ratio * 100:.0f}% of the data...")  # Status
        sample_size = max(100, int(len(all_texts) * sample_ratio))  # Ensure minimum size
        indices = np.random.choice(len(all_texts), sample_size, replace=False)  # Random indices
        all_texts = [all_texts[i] for i in indices]  # Subsample texts
        all_labels = [all_labels[i] for i in indices]  # Subsample labels
    
    print(f"Loaded {len(all_texts)} text samples.")  # Report size
    return all_texts, all_labels  # Return dataset

# --- Metrics Computation ---  # Evaluation metrics for Trainer
def compute_metrics(eval_pred):  # Metric function signature expected by Trainer
    """Compute regression metrics for evaluation."""  # Docstring
    predictions, labels = eval_pred  # Unpack
    predictions = predictions.squeeze()  # Remove extraneous dims
    
    mse = mean_squared_error(labels, predictions)  # Mean Squared Error
    mae = mean_absolute_error(labels, predictions)  # Mean Absolute Error
    r2 = r2_score(labels, predictions)  # R^2 Score
    
    return {  # Return metrics
        "mse": mse,
        "mae": mae,
        "r2": r2
    }

# --- Main Training Function ---  # Orchestration
def main():  # Entrypoint
    """Main function to orchestrate the training and evaluation pipeline."""  # Docstring
    
    # --- 1. Load and Prepare Data ---  # Data prep
    print("--- Step 1: Loading and Preparing Data ---")  # Banner
    texts, labels = load_bias_data()  # Load dataset
    
    train_texts, val_texts, train_labels, val_labels = train_test_split(  # Train/val split
        texts, labels, test_size=config.TEST_SPLIT_SIZE, random_state=42  # Holdout fraction and seed
    )
    
    # --- 2. Initialize Tokenizer and Model ---  # Model setup
    print("\n--- Step 2: Initializing Tokenizer and Model ---")  # Banner
    tokenizer = AutoTokenizer.from_pretrained(config.CLASSIFIER_MODEL)  # Load tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(  # Load classifier
        config.CLASSIFIER_MODEL, 
        num_labels=1  # For regression  # One output
    )

    # Move model to GPU if available  # Device placement
    if config.USE_CUDA:  # If CUDA
        model.to("cuda")  # Move model

    train_dataset = BiasDataset(train_texts, train_labels, tokenizer)  # Wrap train data
    val_dataset = BiasDataset(val_texts, val_labels, tokenizer)  # Wrap val data

    # --- 3. Define Training Arguments ---  # Trainer args
    print("\n--- Step 3: Defining Training Arguments ---")  # Banner
    training_args = TrainingArguments(  # Initialize args
        output_dir=config.RESULTS_DIR,  # Output path
        num_train_epochs=config.TRAIN_EPOCHS,  # Epochs
        learning_rate=config.LEARNING_RATE,  # LR
        per_device_train_batch_size=config.TRAIN_BATCH_SIZE,  # Train BS
        per_device_eval_batch_size=config.EVAL_BATCH_SIZE,  # Eval BS
        warmup_steps=config.WARMUP_STEPS,  # Warmup
        weight_decay=config.WEIGHT_DECAY,  # WD
        logging_dir=config.LOGS_DIR,  # Logs path
        logging_steps=config.LOGGING_STEPS,  # Log freq
        evaluation_strategy="epoch",  # Eval each epoch
        save_strategy="epoch",  # Save each epoch
        load_best_model_at_end=True,  # Keep best
        metric_for_best_model="mse",  # Select by MSE
        greater_is_better=False,  # Lower is better
        fp16=config.USE_CUDA, # Enable mixed-precision training if on GPU  # Speed up
    )

    # --- 4. Initialize and Run Trainer ---  # Training loop
    print("\n--- Step 4: Initializing and Running Trainer ---")  # Banner
    trainer = Trainer(  # Construct trainer
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    # Train the model  # Start training
    print("Starting training...")  # Status
    trainer.train()  # Run training loop
    print("Training finished.")  # Status

    # --- 5. Evaluate and Save ---  # Eval and persist
    print("\n--- Step 5: Evaluating and Saving Model ---")  # Banner
    eval_results = trainer.evaluate()  # Evaluate on validation set
    print("Evaluation results:")  # Header
    for key, value in eval_results.items():  # Iterate metrics
        print(f"  {key}: {value:.4f}")  # Pretty print

    # Save the best model  # Persist best weights
    if os.path.exists(config.TRAINED_MODEL_DIR):  # If a prior model exists
        print(f"Removing existing model at {config.TRAINED_MODEL_DIR}")  # Warn
        os.system(f"rm -rf {config.TRAINED_MODEL_DIR}")  # Remove (POSIX-specific)

    print(f"Saving the best model to {config.TRAINED_MODEL_DIR}...")  # Status
    trainer.save_model(config.TRAINED_MODEL_DIR)  # Save model
    tokenizer.save_pretrained(config.TRAINED_MODEL_DIR)  # Save tokenizer
    
    print("\n--- Training Pipeline Complete ---")  # Footer

if __name__ == "__main__":  # CLI entrypoint
    main()  # Run training
```

---

## vector_store.py

Overview: Creates and manages the embedding-based vector store, builds a NetworkX knowledge graph linking scenarios and dialogues (with bias levels), supports similarity search, querying neighboring nodes, sampling examples by bias level, visualizing a subgraph, and saving/loading the store.

```1:315:vector_store.py
import json  # JSON parsing for dataset files
import os  # Filesystem utilities
import re  # Regular expressions for parsing bias levels
import numpy as np  # (Imported but not directly used) numerical ops
from sentence_transformers import SentenceTransformer  # Embedding model
import networkx as nx  # Knowledge graph structure
import matplotlib.pyplot as plt  # Visualization
from sklearn.metrics.pairwise import cosine_similarity  # Similarity computation
import pickle  # Serialization
import config  # Settings

class BiasVectorStore:  # Vector store with graph augmentation
    def __init__(self, model_name=config.RETRIEVAL_MODEL):  # Constructor
        self.model = SentenceTransformer(model_name)  # Load embeddings model
        self.vectors = {}  # Map: key -> vector
        self.texts = {}  # Map: key -> raw text
        self.bias_types = {}  # Map: key -> bias type string
        self.graph = nx.Graph()  # Undirected graph of nodes/edges
        
    def _parse_bias_level(self, version_string):  # Extract numeric bias from label
        """Extracts bias percentage from version string using regex."""  # Docstring
        match = re.search(r'\((\d+)%\)', version_string)  # Find digits inside parentheses before %
        if match:  # If pattern found
            return int(match.group(1))  # Return int percentage
        return 0 # Default to 0 if no match is found  # Fallback for unknown labels

    def load_data(self, data_dir=config.DATA_DIR):  # Load dataset and build vectors + graph
        """Load data from JSON files and create embeddings"""  # Docstring
        for filename in os.listdir(data_dir):  # Iterate files
            if filename.startswith("bias_data_for_type_") and filename.endswith(".json"):  # Filter
                bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]  # Extract type key
                
                filepath = os.path.join(data_dir, filename)  # Full path
                with open(filepath, 'r', encoding='utf-8') as f:  # Open file
                    data = json.load(f)  # Load list of scenarios
                    
                    for item_idx, item in enumerate(data):  # Each scenario item
                        scenario = item["parameters"]["scenario"]  # Scenario text
                        
                        # Store the scenario text and its embedding  # Scenario node
                        scenario_key = f"{bias_type}_scenario_{item_idx}"  # Unique key
                        scenario_vector = self.model.encode(scenario)  # Embed scenario
                        
                        self.vectors[scenario_key] = scenario_vector  # Save vector
                        self.texts[scenario_key] = scenario  # Save text
                        self.bias_types[scenario_key] = bias_type  # Save type
                        
                        # Add node to graph  # Scenario node with attributes
                        self.graph.add_node(scenario_key, 
                                           text=scenario, 
                                           type="scenario", 
                                           bias_type=bias_type)
                        
                        # Process conversations  # Add dialogue nodes
                        for conv_idx, conversation in enumerate(item["parameters"]["conversations"]):  # Enumerate versions
                            version = conversation["version"]  # Version label
                            dialogues = conversation["dialogues"]  # List of lines
                            
                            # Use regex to get bias level  # Parse bias percent
                            bias_level = self._parse_bias_level(version)  # Numeric bias level
                            
                            # Create a single text from dialogues  # Concatenate dialogue text
                            dialogue_text = " ".join(dialogues)  # Single string
                            dialogue_key = f"{bias_type}_dialogue_{item_idx}_{conv_idx}"  # Unique key
                            dialogue_vector = self.model.encode(dialogue_text)  # Embed dialogue
                            
                            self.vectors[dialogue_key] = dialogue_vector  # Save vector
                            self.texts[dialogue_key] = dialogue_text  # Save text
                            self.bias_types[dialogue_key] = bias_type  # Save type
                            
                            # Add node to graph  # Dialogue node with bias level
                            self.graph.add_node(dialogue_key, 
                                               text=dialogue_text,
                                               type="dialogue",
                                               bias_type=bias_type,
                                               bias_level=bias_level)
                            
                            # Connect dialogue to its scenario  # Edge with weight
                            self.graph.add_edge(scenario_key, dialogue_key, 
                                              relationship="has_example",
                                              weight=bias_level/100.0)
        
        # Add connections between similar scenarios  # Similarity edges
        self._add_similarity_connections()  # Compute and connect
        
        print(f"Loaded {len(self.vectors)} items into the vector store")  # Store size
        print(f"Graph has {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")  # Graph stats
    
    def _add_similarity_connections(self, threshold=config.SIMILARITY_THRESHOLD):  # Connect similar scenarios
        """Add edges between similar scenarios based on cosine similarity"""  # Docstring
        scenario_keys = [k for k in self.vectors.keys() if k.endswith("scenario_0")]  # Pick first scenario per type as exemplar
        
        for i, key1 in enumerate(scenario_keys):  # Outer loop
            vec1 = self.vectors[key1]  # Vector 1
            
            for j, key2 in enumerate(scenario_keys[i+1:], i+1):  # Compare with later keys
                vec2 = self.vectors[key2]  # Vector 2
                
                # Calculate similarity  # Cosine sim
                sim = cosine_similarity([vec1], [vec2])[0][0]  # Scalar sim
                
                if sim > threshold:  # Above cut-off
                    # Add edge between similar scenarios  # Connect nodes
                    self.graph.add_edge(key1, key2, 
                                      relationship="similar_to",
                                      weight=sim)
    
    def search(self, query, top_k=5):  # Retrieve similar scenarios
        """
        Search for the most similar scenarios to the query.
        This function is optimized to only return scenario-level texts.
        """  # Docstring
        query_vector = self.model.encode(query)  # Embed query
        
        # Calculate similarities, but only for scenarios  # Filter to scenarios
        scenario_similarities = {}  # Map key -> sim
        for key, vector in self.vectors.items():  # Iterate all vectors
            if "scenario" in key:  # Only scenario nodes
                sim = cosine_similarity([query_vector], [vector])[0][0]  # Cosine sim
                scenario_similarities[key] = sim  # Save
        
        # Sort by similarity  # Rank results
        sorted_items = sorted(scenario_similarities.items(), key=lambda x: x[1], reverse=True)  # Descending
        
        # Return top k results  # Assemble results
        results = []  # List of dicts
        for key, sim in sorted_items[:top_k]:  # Take top k
            results.append({
                "key": key,  # Node key
                "text": self.texts[key],  # Scenario text
                "similarity": sim,  # Cosine score
                "bias_type": self.bias_types[key]  # Bias type
            })
        
        return results  # Return list
    
    def query_knowledge_graph(self, query, top_k=3):  # Retrieve nodes and their neighbors
        """Find relevant information using the knowledge graph"""  # Docstring
        # First, find the most similar nodes to the query  # Reuse search
        query_results = self.search(query, top_k=top_k)  # Get top scenarios
        
        graph_results = []  # Aggregate output
        for result in query_results:  # For each scenario
            key = result["key"]  # Node key
            
            # Get node information  # Node attrs
            node_data = self.graph.nodes[key]  # Node dict
            
            # Get connected nodes  # Gather neighbors
            neighbors = []  # List of neighbor dicts
            for neighbor in self.graph.neighbors(key):  # Iterate edges
                edge_data = self.graph.get_edge_data(key, neighbor)  # Edge attrs
                neighbor_data = self.graph.nodes[neighbor]  # Neighbor attrs
                
                neighbors.append({  # Append summarized neighbor
                    "key": neighbor,
                    "text": neighbor_data.get("text", ""),
                    "type": neighbor_data.get("type", ""),
                    "relationship": edge_data.get("relationship", ""),
                    "bias_level": neighbor_data.get("bias_level", None)
                })
            
            graph_results.append({  # Summarize root node and neighbors
                "key": key,
                "text": node_data.get("text", ""),
                "type": node_data.get("type", ""),
                "bias_type": node_data.get("bias_type", ""),
                "neighbors": neighbors
            })
        
        return graph_results  # List of node summaries
    
    def get_bias_examples(self, query, bias_level=None):  # Extract dialogue examples filtered by level
        """Get examples of bias at a specific level for a query"""  # Docstring
        # First, find similar scenarios  # Seed from search
        similar_scenarios = self.search(query, top_k=3)  # Top scenarios
        
        examples = []  # Aggregate examples
        for scenario in similar_scenarios:  # For each scenario
            scenario_key = scenario["key"]  # Node key
            # Ensure we are starting from a scenario node  # Guard
            if "scenario" not in scenario_key:  # Must be scenario
                continue  # Skip non-scenarios
            
            # Find dialogues connected to this scenario  # Explore neighbors
            for neighbor in self.graph.neighbors(scenario_key):  # Iterate neighbors
                neighbor_data = self.graph.nodes[neighbor]  # Neighbor attrs
                
                # Skip if not a dialogue  # Only dialogues
                if neighbor_data.get("type") != "dialogue":
                    continue  # Ignore non-dialogues
                
                # Skip if bias level doesn't match (if specified)  # Filter by level
                if bias_level is not None and neighbor_data.get("bias_level") != bias_level:
                    continue  # Skip level mismatch
                
                examples.append({  # Add example
                    "scenario": scenario["text"],  # Scenario text
                    "dialogue": neighbor_data.get("text", ""),  # Dialogue text
                    "bias_level": neighbor_data.get("bias_level", 0),  # Level
                    "bias_type": scenario["bias_type"]  # Type
                })
        
        return examples  # Return list
    
    def visualize_graph(self, save_path="static/knowledge_graph.png"):  # Draw sample of graph
        """Visualize a portion of the knowledge graph"""  # Docstring
        # Create a smaller subgraph for visualization  # Avoid clutter
        subgraph_nodes = list(self.graph.nodes())[:config.GRAPH_NODE_COUNT_LIMIT]  # First N nodes
        subgraph = self.graph.subgraph(subgraph_nodes)  # Induced subgraph
        
        plt.figure(figsize=(14, 12))  # Figure size
        
        # Set node colors based on type  # Color coding
        node_colors = []  # Colors list
        for node in subgraph.nodes():  # Iterate nodes
            node_type = self.graph.nodes[node].get("type")  # Type
            if node_type == "scenario":  # Scenario color
                node_colors.append("skyblue")
            elif node_type == "dialogue":  # Dialogue color by bias level
                # Color dialogues based on bias level  # Legend
                bias_level = self.graph.nodes[node].get("bias_level", 0)  # Level
                if bias_level < 30:
                    node_colors.append("#90ee90") # LightGreen  # Low bias
                elif bias_level < 70:
                    node_colors.append("#ffd700") # Gold  # Moderate bias
                else:
                    node_colors.append("#f08080") # LightCoral  # High bias
            else:  # Fallback
                node_colors.append("grey")
        
        # Create layout  # Node positions
        pos = nx.spring_layout(subgraph, k=0.5, iterations=50)  # Force-directed layout
        
        # Draw nodes and edges  # Render elements
        nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, alpha=0.9, node_size=600)  # Nodes
        nx.draw_networkx_edges(subgraph, pos, alpha=0.2, edge_color="gray")  # Edges
        
        # Draw labels with shortened text  # Truncated labels for readability
        labels = {}  # Node labels
        for node in subgraph.nodes():  # Iterate nodes
            text = self.graph.nodes[node].get("text", "")  # Node text
            node_type = self.graph.nodes[node].get("type", "")  # Node type
            label_text = f"[{node_type.upper()}]\n" + (text[:30] + "..." if len(text) > 30 else text)  # Compose label
            labels[node] = label_text  # Assign label
        
        nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=8, verticalalignment='center_baseline')  # Draw labels
        
        plt.title("Bias Knowledge Graph (Sample View)", fontsize=16)  # Title
        plt.axis("off")  # Hide axes
        
        # Create directory if it doesn't exist  # Ensure output path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Create dirs
        
        plt.tight_layout()  # Optimize layout
        plt.savefig(save_path, dpi=300, bbox_inches='tight')  # Save image
        plt.close()  # Close figure
        
        return save_path  # Return path
    
    def save(self, filepath=config.VECTOR_STORE_PATH):  # Persist store to disk
        """Save the vector store to a file"""  # Docstring
        # Ensure directory exists, but only if a directory is specified in the path  # Guard
        dir_name = os.path.dirname(filepath)  # Directory name
        if dir_name:  # If non-empty
            os.makedirs(dir_name, exist_ok=True)  # Create directories
        
        with open(filepath, 'wb') as f:  # Open file for binary write
            pickle.dump(self, f)  # Serialize whole object
        print(f"Vector store saved to {filepath}")  # Log
    
    def load(self, filepath=config.VECTOR_STORE_PATH):  # Load store from disk
        """Load the vector store from a file"""  # Docstring
        with open(filepath, 'rb') as f:  # Open binary
            store = pickle.load(f)  # Deserialize object
        self.__dict__.update(store.__dict__)  # Copy state
        print(f"Vector store loaded from {filepath}")  # Log


def get_vector_store(force_rebuild=False):  # Helper to get or build store
    """Get the vector store, building it if necessary"""  # Docstring
    if os.path.exists(config.VECTOR_STORE_PATH) and not force_rebuild:  # If cache exists
        print("Loading existing vector store...")  # Log
        store = BiasVectorStore()  # Create empty instance
        store.load()  # Load saved state
        return store  # Return store
    else:  # Build from scratch
        print("Building new vector store...")  # Log
        store = BiasVectorStore()  # Create new instance
        store.load_data()  # Load data and build
        store.save()  # Save to disk
        return store  # Return new store


if __name__ == "__main__":  # CLI example usage
    # Example usage  # Header
    vector_store = get_vector_store()  # Load/build store
    
    # Test search  # Demonstrate search API
    search_results = vector_store.search("gender discrimination in workplace", top_k=3)  # Query
    print("\nSearch Results:")  # Header
    for result in search_results:  # Iterate results
        print(f"- {result['text'][:100]}... (Similarity: {result['similarity']:.4f})")  # Preview
    
    # Test knowledge graph query  # Demonstrate graph API
    graph_results = vector_store.query_knowledge_graph("race and cultural bias")  # Query graph
    print("\nKnowledge Graph Results:")  # Header
    for result in graph_results:  # Iterate nodes
        print(f"- {result['text'][:100]}...")  # Preview text
        print(f"  Type: {result['type']}, Bias Type: {result['bias_type']}")  # Node meta
        print(f"  {len(result['neighbors'])} connected nodes")  # Degree
    
    # Visualize graph  # Render subgraph
    graph_path = vector_store.visualize_graph()  # Save figure
    print(f"\nGraph visualization saved to {graph_path}")  # Report path
```

---

## Notes

- Ensure `config.ini` contains a valid Hugging Face token under section `[huggingface]` with key `token`.
- Build assets first: `python preprocess_data.py` (will prompt if a cache exists)
- Optionally pre-download the model: `python download_model.py`
- Run the app: `python app.py`
