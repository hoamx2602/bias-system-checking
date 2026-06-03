import torch

# --- File Paths ---
DATA_DIR = "dataset"
VECTOR_STORE_PATH = "bias_vector_store.pkl"
TRAINED_MODEL_DIR_INTENSITY = "models/bias_classifier/intensity"
TRAINED_MODEL_DIR_TYPE = "models/bias_classifier/type"
RESULTS_DIR = "results"
LOGS_DIR = "logs"
EVALUATION_RESULTS_DIR = "evaluation_results"
KNOWLEDGE_GRAPH_IMAGE_PATH = "static/knowledge_graph.png"

# --- Model Configuration ---
# Model for semantic search and context retrieval
RETRIEVAL_MODEL = "sentence-transformers/all-mpnet-base-v2"
# Generative model for answering questions based on context
GENERATIVE_MODEL = "google/gemma-3-1b-it"
# Optional: A classifier model for a supplemental bias score (can be trained via train.py)
CLASSIFIER_MODEL = "distilbert-base-uncased"

# --- Vector Store & Knowledge Graph ---
SIMILARITY_THRESHOLD = 0.65  # For connecting similar scenarios in the graph
GRAPH_NODE_COUNT_LIMIT = 50   # Max nodes for visualization to keep it readable

# --- Training Hyperparameters (for train.py) ---
USE_PRETRAINED_CLASSIFIER = True
TRAIN_SAMPLE_RATIO = 1.0  # Use 100% of data for training
TEST_SPLIT_SIZE = 0.2
TRAIN_EPOCHS = 100
TRAIN_BATCH_SIZE = 4 if not torch.cuda.is_available() else 8  # Smaller batch for CPU
EVAL_BATCH_SIZE = 4 if not torch.cuda.is_available() else 8   # Smaller batch for CPU
WARMUP_STEPS = 500
WEIGHT_DECAY = 0.01
LOGGING_STEPS = 50
LEARNING_RATE = 5e-5

# --- Application Settings ---
# Set to True if a GPU is available, False otherwise
USE_CUDA = torch.cuda.is_available()
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
"""

# --- Evaluation Settings ---
EVALUATION_QUESTIONS = [
    "What are the risks of overlooking contributions from women in tech?",
    "How can stereotypes about age affect hiring decisions for older candidates?",
    "Why is it problematic to assume someone's capabilities based on their accent?",
    "Describe a scenario where social class bias might appear in a professional setting.",
    "How might an AI recruitment tool develop a bias against candidates from non-traditional educational backgrounds?",
    "What kind of intersectional bias might a disabled woman from a racial minority face in the workplace?",
    "Explain how confirmation bias can affect a manager's performance review of an employee.",
    "In what ways can regional stereotypes lead to unfair treatment in a national company?"
] 