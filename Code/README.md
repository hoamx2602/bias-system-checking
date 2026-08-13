# AI-Based Bias Detection & Ethical Analysis System

A complete Retrieval-Augmented Generation (RAG) pipeline that detects, classifies and explains social bias in natural-language text.  The project combines large-scale curated datasets, transformer models, a similarity-based **vector store**, a graph-structured **knowledge base**, and a Flask web interface to deliver end-to-end bias analysis.

> **Flowchart** See `src/app/static/bias_design_flow.jpg` for the high-level execution flow referenced throughout this document.  Each numbered step in the diagram is mapped to concrete code in the *Implementation Checklist* section.

---

## Table of Contents
1.  [Quick Start](#quick-start)
2.  [Architecture Overview](#architecture-overview)
3.  [Model Architecture & Rationale](#model-architecture--rationale)
4.  [Repository Layout](#repository-layout)
5.  [Datasets](#datasets)
6.  [Pre-processing & Knowledge-Asset Building](#pre-processing--knowledge-asset-building)
7.  [Training Pipeline](#training-pipeline)
8.  [Vector Store & Knowledge Graph](#vector-store--knowledge-graph)
9.  [Bias-Analysis RAG Pipeline](#bias-analysis-rag-pipeline)
10. [Web Application](#web-application)
11. [API Endpoints](#api-endpoints)
12. [Evaluation Utilities](#evaluation-utilities)
13. [Configuration](#configuration)
14. [Implementation Checklist ⇄ Flowchart](#implementation-checklist-flowchart)
15. [Sample Questions](#sample-questions)
16. [Troubleshooting & FAQs](#troubleshooting--faqs)
17. [Extending the System](#extending-the-system)

---

## Quick Start
```bash
# 1.  (Recommended) create a virtual environment
$ python -m venv .venv
$ source .venv/Scripts/activate        # Windows
# source .venv/bin/activate            # macOS / Linux

# 2.  Install project requirements
$ pip install -r requirements.txt

# 3.  Download the generative LLM (≈ 8 GB) – can be run overnight
$ python run_download_model.py         # requires a valid HF token in .env (see .env.example)

# 4.  Build knowledge assets (vector store + graph visual)
$ python run_preprocess.py             # prompts before rebuilding if cache exists

# 5.  Fire-up the web server
$ python run_app.py                    # visit  http://localhost:5001
```

> **Windows Users** Before running `run_download_model.py`, you must enable **Developer Mode** so that the Hugging Face Hub can create symlinks for its model cache.
> Go to **Settings → Privacy & security → For developers → Developer Mode → On**.
> Without this, the download will fail with `[WinError 1314] A required privilege is not held by the client`.

> **Note** GPU acceleration is detected automatically (`config.USE_CUDA`).  CPU-only execution is possible but slower.

---

## Architecture Overview
![Design Flow](src/app/static/bias_design_flow.jpg)

The flowchart above depicts the end-to-end data path:

1. **User Prompt** – A user submits a free-text question via the web UI.
2. **Embedding & Vector Store** – The text is embedded with Sentence-Transformers and compared against scenario vectors in `bias_vector_store.pkl`.
3. **Knowledge Graph** – Connected dialogues and bias metadata are fetched, forming a context bundle ("Bias Brief").
4. **Prompt Assembly** – The brief plus user question are assembled into Gemma 3 chat messages.
5. **Large Language Model** – The Gemma 3 instruction-tuned LLM generates a context-grounded, bias-aware answer.
6. **Output Rendering** – The UI visualises the answer, bias gauge, and relevant graph snapshot.

Each block is colour-coded and numbered identically to the *Implementation Checklist* for 1-to-1 traceability.

---

## Model Architecture & Rationale

### 1. Sentence-Transformers — `all-mpnet-base-v2` (Retrieval Encoder)
- **Role**  Encodes every scenario and user query into a 768-D dense vector for semantic search.
- **Architecture**  Encoder-only Transformer (MPNet) wrapped by Sentence-Transformers bi-encoder fine-tuning.
- **Why chosen**  SOTA semantic performance at manageable size; CPU-friendly; multilingual coverage.
- **Code locations**  `src/data/vector_store.py → BiasVectorStore.__init__`, `.load_data()`, `.search()`.

### 2. Knowledge-Graph (NetworkX)
- Although not an ML model, the undirected graph built in `src/data/vector_store.py` provides structural explainability.
- **Nodes**: scenarios & dialogues  **Edges**: `has_example` (bias level), `similar_to` (cosine sim).
- Visualised via `BiasVectorStore.visualize_graph()` → `src/app/static/knowledge_graph.png`.

### 3. Gemma 3 (google/gemma-3-1b-it) – Generative LLM
- **Role**  Generates the final, context-grounded answer.
- **Model card**  [Gemma 3 1B IT on Hugging Face](https://huggingface.co/google/gemma-3-1b-it)
- **Why chosen**  Lightweight, multimodal-capable family with strong instruction-following; supports chat templates via Transformers ≥ 4.50.0.
- **Code locations**  `src/inference/pipeline.py → BiasAnalysisPipeline.__init__` (model load) & `.analyze()` (generation).
- **Generation params**  `max_new_tokens≈300`, `temperature=0.7`, `top_p=0.95`, beam search 5, with chat template via `tokenizer.apply_chat_template`.

### 4. DistilBERT (Optional Bias-Score Regressor)
- **Role**  Predicts a scalar bias intensity (0-1) for dialogue snippets.
- **Architecture**  6-layer encoder with regression head.
- **Training**  `python run_train.py`; metrics MSE/MAE/R²; checkpoint saved to `models/bias_classifier/`.
- Not loaded by default in the web app but can augment `/analyze` responses.

### 5. End-to-End Model Flow
1. **Embed** user question with Sentence-Transformers.
2. **Retrieve** top-k scenarios via cosine similarity.
3. **Assemble** chat messages (`config.PROMPT_TEMPLATE` → `apply_chat_template`).
4. **Generate** answer with Gemma 3 (1B IT).
5. *(Optional)* **Score** bias with DistilBERT.

> GPU acceleration is auto-detected (`config.USE_CUDA`). All models fall back to CPU when CUDA is unavailable.

---

## Repository Layout
```
├── run_app.py                 # Entry-point: starts the Flask web app
├── run_train.py               # Entry-point: trains the bias classifiers
├── run_preprocess.py          # Entry-point: builds the vector store & graph visual
├── run_download_model.py      # Entry-point: offline download helper for the LLM
├── run_mitigation_metrics.py  # Entry-point: reference-free mitigation evaluation
├── run_ablation.py            # Entry-point: bias-level label-fix ablation study
├── run_hf_debug.py            # Entry-point: HF token / model-access diagnostics
├── src/
│   ├── config.py              # Centralised settings (paths, models, hyper-params)
│   ├── data/
│   │   ├── vector_store.py    # Embedding, similarity search & graph utilities
│   │   └── preprocess.py      # Builds vector store & graph visual
│   ├── inference/
│   │   └── pipeline.py        # Retrieval-Augmented Generation (RAG) pipeline
│   ├── training/
│   │   ├── train.py           # Bias-regression / classification training
│   │   └── ablation.py        # Label-fix ablation study
│   ├── evaluation/
│   │   └── mitigation_metrics.py  # Reference-free mitigation-quality metrics
│   ├── app/
│   │   ├── server.py          # Flask application & routes
│   │   ├── templates/         # Jinja2 HTML templates (UI)
│   │   └── static/            # Images: graph visual, bias gauge, design flow
│   └── scripts/
│       ├── download_model.py  # Offline download helper for the LLM
│       └── hf_debug.py        # HF token / model-access diagnostics
├── dataset/                   # 11 JSON files with multi-level bias examples
├── evaluation_results/        # Stored evaluation metrics & figures
├── requirements.txt           # Python dependencies
└── config.ini / .env          # Secrets (HF token) — see .env.example
```

*(files inside `.venv/`, `@.hf_cache/`, `models/`, `results/`, `logs/` are intentionally ignored)*

---

## Datasets
• **Source** Synthetic + curated real-world examples grouped into **11 bias categories** (Personal Identity, Social, Professional & Educational, …, Misc).
• **Granularity** Each scenario contains 6 dialogue versions labelled *No Bias (0 %) → Extreme (100 %)*.
• **Statistics**
  – >30 k dialogues   – 11 bias types   – 6 scalar bias levels

> Call `analyze_dataset_stats()` in `src/data/preprocess.py` for a live summary.

---

## Pre-processing & Knowledge-Asset Building
Script `src/data/preprocess.py` (entry-point: `run_preprocess.py`)
1. Parses every JSON file in `dataset/`.
2. Encodes scenario & dialogue texts with **Sentence-Transformers** (`all-mpnet-base-v2`).
3. Stores embeddings + metadata in a Python `pickle` (`bias_vector_store.pkl`).
4. Builds an **undirected graph** (`networkx`):
   • Nodes: scenarios & dialogues • Edges: *has_example*, *similar_to*
5. Saves a PNG visual (`src/app/static/knowledge_graph.png`).

Re-running the script will detect an existing cache and ask whether to rebuild.

---

## Training Pipeline
Script `src/training/train.py` (entry-point: `run_train.py`) *(optional – pre-trained DistilBERT works out-of-the-box)*
1. Loads text/label pairs (`load_bias_data`).
2. Splits 80 / 20 into train/val (`scikit-learn`).
3. Fine-tunes a **DistilBERT** regression head on scalar bias (0–1).
4. Logs MSE, MAE, R², stores best model in `models/bias_classifier/`.

Hyper-parameters are centralised in `src/config.py` – tweak epochs, batch-size, LR, etc.

---

## Vector Store & Knowledge Graph
Module `src/data/vector_store.py`
• **Embedding** Sentence-Transformers via `SentenceTransformer` API.
• **Similarity** Cosine, threshold = 0.65 for inter-scenario edges.
• **API**
  – `search(query, top_k)`          → returns similar scenarios
  – `query_knowledge_graph(query)`   → sub-graph with neighbours
  – `get_bias_examples(query, level)` → dialogue examples @ desired bias level
• **Visualisation** `visualize_graph()` generates the PNG used in UI.

![Knowledge Graph](src/app/static/knowledge_graph.png)

---

## Bias-Analysis RAG Pipeline
Module `src/inference/pipeline.py`
1. **Retrieval** Calls `vector_store.search()` with the user question.
2. **Prompt Construction** Builds Gemma 3 chat messages using `config.PROMPT_TEMPLATE`.
3. **Generation** Feeds chat-formatted inputs to **Gemma 3 (1B IT)** via `AutoModelForCausalLM.generate`.
4. **Return Structure**
```json
{
  "answer":          "LLM-generated neutral explanation…",
  "source_contexts": ["…"],
  "bias_type":       "social_bias"
}
```

A singleton (`get_analysis_pipeline`) caches the model & store to avoid reload overhead.

---

## Web Application
Entry `src/app/server.py` (Flask, entry-point: `run_app.py`)
• `/` Main UI (`src/app/templates/index.html`) – text box, *Analyze Bias* button, gauge & graph image.
• `/analyze` (POST) JSON API powering the button; delegates to `analysis_pipeline.analyze()`.
• `/evaluation` Manual QA page running predefined questions.
• Static resources (graph, gauges) served via `/static/<file>`.

Run on `0.0.0.0:5001` – change port in `src/app/server.py` (`main()`) if required.

---

## API Endpoints
| Method | Route | Payload / Params | Description |
|-------:|-------|------------------|-------------|
| `GET`  | `/` | – | Serves the main HTML interface |
| `POST` | `/analyze` | `{ "question": "..." }` | Core RAG endpoint – returns JSON with `answer`, `source_contexts`, `bias_type` |
| `GET`  | `/evaluation` | – | Displays manual evaluation page |
| `POST` | `/run_evaluation` | – | Batch-runs RAG answers for the preset questions in `src/config.py` |
| `POST` | `/run_mitigation_evaluation` | `{ "limit": 12, "seed": 42 }` or `{ "score_file": "..." }` | Reference-free mitigation scoring – bias reduction, content preservation, type consistency |
| `GET`  | `/static/<path>` | – | Serves static assets (graph, gauge, CSS) |

All responses are UTF-8 encoded JSON except for static/HTML routes.

---

## Evaluation Utilities
* `src/app/templates/metrics.html`, `evaluation_results/metrics.json`
* Confusion matrix (`confusion_matrix.png`) for the optional classifier.
* `/run_evaluation` endpoint automates RAG-based responses over `config.EVALUATION_QUESTIONS`.

### Reference-based metrics (`src/app/server.py`)
BLEU-1…4, ROUGE-1/2/L and semantic similarity, compared against the hand-written
`reference_answer` entries in `EVALUATION_TARGETS`. Because every item needs a reference,
this only covers the 8 questions in `config.EVALUATION_QUESTIONS`. Output:
`evaluation_results/rag_metrics.json`.

### Reference-free mitigation metrics (`src/evaluation/mitigation_metrics.py`)
Measures whether the generated rewrite actually removes the bias, using the trained
supervised heads instead of a reference answer — so any dialogue in `dataset/` is a valid
evaluation item.

| Signal | Definition |
|--------|------------|
| **Bias Reduction (Δ)** | `intensity(input) − intensity(mitigation)` from the intensity regressor |
| **Content Preservation** | cosine similarity between input and mitigation on `all-mpnet-base-v2` |
| **Type Consistency** | whether the predicted bias type changes after rewriting |

The three only mean something together. A large Δ is not success on its own: the generator
can drive the intensity to zero by writing about something else, which shows up as a high
Δ with low similarity. The aggregate reports those separately:

* `clean_mitigation_rate` — bias down **and** still on topic (the real success rate)
* `gamed_rate` — bias down **but** off topic
* `unchanged` / `amplified` rates, plus breakdowns by predicted input intensity band and by bias type

Neutral inputs (intensity ≤ 0.15) have no bias to remove, so they are excluded from the Δ
averages and reported as a separate count — they act as controls for over-rewriting.

```bash
# end-to-end: one full generation per sample
python run_mitigation_metrics.py --limit 12

# cheap: re-score pairs that were already generated
python run_mitigation_metrics.py --score-file evaluation_results/rag_metrics.json
```

Output: `evaluation_results/mitigation_metrics.json`, rewritten after every sample so an
interrupted run is not lost.

#### Pinned judge — required before retraining on expanded data

Δ is the intensity model's *opinion* of a text. Retraining that model changes every Δ even
though the generator is untouched, so `+33 pts` measured before a retrain and `+41 pts`
measured after are **not comparable** — the ruler moved, not the generator.

To keep numbers comparable across dataset versions (e.g. when a new domain such as
Procurement is added), snapshot the current heads and always score against that snapshot:

```bash
# 1. BEFORE retraining — freeze the current heads as a judge
python run_mitigation_metrics.py --pin-judge models/bias_classifier_judge_v1

# 2. Establish the baseline against the pinned judge
python run_mitigation_metrics.py --judge-dir models/bias_classifier_judge_v1 --limit 50

# 3. Expand dataset, retrain (run_train.py), then re-measure with the SAME judge
python run_mitigation_metrics.py --judge-dir models/bias_classifier_judge_v1 --limit 50
```

Every report records which heads produced its numbers under `scored_by`, including a
`comparable_across_retrains` flag — a file of deltas is unattributable without it. Runs that
use the production heads are stamped `"scorer": "production"` and flagged as not comparable.

`--pin-judge` refuses to overwrite an existing judge unless `--force` is passed, since
overwriting invalidates every baseline already measured against it. Note that `models/` is
in `.gitignore`: the judge snapshot is **not** version-controlled, so back it up if the
baselines matter.

What still needs redoing after each retrain, and what does not:

| On dataset expansion + retrain | Redo? | Why |
|---|:---:|---|
| Re-run baseline Δ | Yes | New input distribution; use the pinned judge so it stays comparable |
| Re-check similarity distribution | Yes | New text shapes shift the distribution |
| Recalibrate `BIAS_REDUCTION_FLOOR` | Yes | Tied to the intensity model's MAE — read the new `eval_mae` |
| Recalibrate `CONTENT_SIMILARITY_FLOOR` | Maybe | Only if the similarity distribution shifted materially |
| Worry about the similarity *scale* | No | `all-mpnet-base-v2` is frozen and never fine-tuned |

> Caveat: the intensity regressor's own validation MAE is ≈0.126, so a single Δ is noisy.
> `BIAS_REDUCTION_FLOOR` (0.10) keeps borderline pairs in `unchanged` rather than counting
> them as wins, but the aggregate rates are the trustworthy part, not per-sample verdicts.
> Breakdowns are keyed on *predicted* input intensity, not the dataset version strings,
> because `parse_bias_percentage()` defaults ~30% of the corpus to 50%.

---

## Configuration
Settings live in **two** files:
1. `src/config.py` – technical knobs (paths, models, hyper-params).
2. `.env` (copy from `.env.example`) – *private* secrets (Hugging-Face token). **Add your token** as
```
[huggingface]
token = hf_XXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Implementation Checklist ⇄ Flowchart
| # | Flowchart Step | Implementing File(s)/Function(s) | Status |
|---|----------------|----------------------------------|:------:|
| 0 | Build vector store & graph (offline) | `src/data/preprocess.py`, `src/data/vector_store.py` | ✓ |
| 1 | User enters question in web UI | `src/app/templates/index.html`, `<form id="analyze-form">` | ✓ |
| 2 | Flask receives request | `src/app/server.py → /analyze` | ✓ |
| 3 | Retrieve similar scenarios | `src.data.vector_store.BiasVectorStore.search()` | ✓ |
| 4 | Assemble prompt with context | `src.inference.pipeline.BiasAnalysisPipeline.analyze()` | ✓ |
| 5 | Generate answer with Gemma 3 | `transformers.AutoModelForCausalLM` in `src/inference/pipeline.py` | ✓ |
| 6 | Return bias type & source contexts | `src/inference/pipeline.py` (dict return) | ✓ |
| 7 | Render gauge & graph | `src/app/templates/index.html`, `src/app/static/bias_gauge.png`, `src/app/static/knowledge_graph.png` | ✓ |
| 8 | Train optional classifier | `src/training/train.py` (`run_train.py`) | ✓ |
| 9 | Evaluate pipeline | `src/app/server.py → /run_evaluation`, `evaluation_results/` | ✓ |

All boxes in the provided flowchart have a corresponding checked implementation in the repository.

---

## Sample Questions
Below are a handful of illustrative questions you can copy-paste into the web UI (or `/analyze` API) to see the system in action.

| # | Example Question |
|---|------------------|
| 1 | Why is it problematic to assume someone's capabilities based on their accent? |
| 2 | How can stereotypes about age affect hiring decisions for older candidates? |
| 3 | Describe a scenario where social-class bias might appear in a professional setting. |
| 4 | Explain how confirmation bias can affect a manager's performance review of an employee. |
| 5 | What kind of intersectional bias might a disabled woman from a racial minority face in the workplace? |
| 6 | What challenges can arise when employees with chronic illnesses request flexible working arrangements? |
| 7 | How might assumptions about political beliefs create tension within a diverse project team? |
| 8 | In what ways can parental-status bias affect career progression for single parents? |
| 9 | Why is favouring graduates from elite universities during recruitment considered educational bias? |
| 10 | What problems occur when AI moderation systems learn biased language from social media? |
| 11 | Describe how high-stress situations during crisis management can amplify situational bias in decision-making. |

---

## Troubleshooting & FAQs
**Q 1:** *`ValueError: Hugging Face token not found`*

Add `HF_TOKEN=your_token` to `Code/.env` (copy from `.env.example`). Tokens are free: https://huggingface.co/settings/tokens

**Q 2:** *CUDA-out-of-memory during LLM load*

Force CPU inference by exporting `CUDA_VISIBLE_DEVICES=` before running `run_app.py` (device selection lives in `src/config.py`).

**Q 3:** *`ModuleNotFoundError: sentence_transformers`*

Run `pip install -r requirements.txt` inside your virtual environment.

**Q 4:** *Vector store takes too long to build*

Run `python run_preprocess.py` *overnight* or on a machine with GPU support – subsequent runs simply un-pickle the store.

---

## Advanced: Training Pipeline Documentation

### What is the Training Script?

The `src/training/train.py` script (entry-point: `run_train.py`) trains a **supplemental bias classifier** - an additional ML model that can predict bias intensity levels in text. This complements the main RAG system by providing quantitative bias scores.

### Purpose & Architecture

- **What it does**: Trains a DistilBERT regression model to predict bias intensity (0-1 scale) from dialogue text
- **Training data**: Uses all bias scenarios from the dataset with their bias level labels
- **Model type**: DistilBERT with regression head (single output neuron for bias score prediction)
- **Integration**: The trained model can be optionally used alongside the main analysis pipeline

### Training Process Walkthrough

#### Step 1: Data Preparation
```python
# Load all conversations from dataset files
texts, labels = load_bias_data()

# Parse bias percentages from version strings:
# - "Version 1: No Bias (0%)" → 0%
# - "Mixed Bias Version 1: Strong Personalities..." → 50% 
# - Extreme bias indicators → 100%
```

#### Step 2: Train/Validation Split
- **80%** training data, **20%** validation data
- Random split with fixed seed for reproducibility

#### Step 3: Model Setup
- **Base model**: `distilbert-base-uncased` (configurable via `config.CLASSIFIER_MODEL`)
- **Architecture**: Classification head repurposed for regression (num_labels=1)
- **Device**: Automatic GPU detection, CPU fallback

#### Step 4: Training Configuration
Default hyperparameters (adjustable in `src/config.py`):
```python
TRAIN_EPOCHS = 3              # Training iterations
TRAIN_BATCH_SIZE = 8          # Batch size per device
LEARNING_RATE = 5e-5          # Optimizer learning rate
TEST_SPLIT_SIZE = 0.2         # Validation split ratio
```

#### Step 5: Evaluation Metrics
- **MSE (Mean Squared Error)**: Primary metric for regression
- **MAE (Mean Absolute Error)**: Average prediction error
- **R² (Coefficient of Determination)**: Model fit quality

### Running Training

```bash
# Basic training (uses all defaults)
python run_train.py

# Training will output:
# - Models cached to @.hf_cache/ directory
# - Progress logs with loss/metrics
# - Final evaluation results
# - Saved model in models/bias_classifier/
```

### Output & Results

**Training artifacts:**
- `models/bias_classifier/` - Full model + tokenizer
- `logs/` - TensorBoard logs (if configured)
- `results/` - Checkpoints and final model

**Evaluation metrics example:**
```
Evaluation results:
  eval_loss: 0.0234
  eval_mse: 0.0234
  eval_mae: 0.1254
  eval_r2: 0.8765
```

### Dataset Compatibility

The training script handles multiple bias data formats:
- ✅ **Percentage format**: "Version 1: No Bias (0%)" 
- ✅ **Mixed bias format**: "Mixed Bias Version 1: Strong Personalities..."
- ✅ **Fallback mapping**: Unknown formats → moderate bias (50%)

### Troubleshooting Training Issues

**Q: ValueError: invalid literal for int() with base 10**

This error occurred before our fix. The training script now handles all bias data formats automatically. If you still encounter issues:

1. Check that dataset files contain the expected JSON structure
2. Ensure version strings follow one of the supported formats
3. Use the fallback parsing logic for unsupported formats

**Q: CUDA out of memory during training**

The batch size automatically reduces to 4 for CPU training. Manual override:
```python
TRAIN_BATCH_SIZE = 2  # Further reduce if needed
EVAL_BATCH_SIZE = 2   # Further reduce if needed
```

**Q: Training takes too long**

Try these optimizations:
```python
TRAIN_SAMPLE_RATIO = 0.5  # Use only 50% of data
TRAIN_EPOCHS = 1          # Reduce to 1 epoch
```

**Q: Symlink warnings during training**

These warnings are automatically suppressed in the training script. You can ignore them safely.

**Q: Pin memory warnings**

The training script is configured to disable pin_memory for CPU training, eliminating these warnings.

### Use Cases & Integration

**Current system**: The main analysis uses RAG (retrieval + generation) without requiring this classifier.

**Potential enhancements** (requires integration work):
- Bias score validation alongside analysis
- Confidence metrics for generated responses  
- Bias intensity quantification for scenarios
- Combined RAG + classifier ensemble for bias detection

### Configuration Options

All training parameters are configurable in `src/config.py`:
```python
# Model Configuration
CLASSIFIER_MODEL = "distilbert-base-uncased"  # Base model to fine-tune

# Training Hyperparameters  
TRAIN_SAMPLE_RATIO = 1.0  # Fraction of data to use (0.0-1.0)
TEST_SPLIT_SIZE = 0.2     # Validation split size
TRAIN_EPOCHS = 3          # Number of training epochs
TRAIN_BATCH_SIZE = 8      # Training batch size
EVAL_BATCH_SIZE = 8       # Evaluation batch size
LEARNING_RATE = 5e-5      # Adam optimizer learning rate
WARMUP_STEPS = 500        # Warmup steps for learning rate scheduler
WEIGHT_DECAY = 0.01       # Weight decay regularization
LOGGING_STEPS = 50        # Steps between logging
```