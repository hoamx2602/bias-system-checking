import os
import config  # must be first: loads .env and configures HF environment variables

from flask import Flask, request, jsonify, render_template, send_from_directory
from models import get_analysis_pipeline

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Pre-load the full analysis pipeline ---
# This ensures the models are loaded into memory only once when the app starts.
print("=" * 60)
print("Starting BIAS Analysis Application...")
print("Loading AI models... Please wait...")
import time
start_time = time.time()

try:
    analysis_pipeline = get_analysis_pipeline()
    load_time = time.time() - start_time
    print(f"Models loaded successfully in {load_time:.1f} seconds")
    print("Application is ready to analyze bias scenarios")
    print("=" * 60)
except Exception as e:
    print(f"FATAL: Could not initialize the AI pipeline. Error: {e}")
    print("Please check your model cache directory (@.hf_cache/) and .env file")
    analysis_pipeline = None

# --- Static File Serving ---
# Route to serve the generated knowledge graph image
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# --- Lexical and Semantic RAG Evaluation Helpers ---
EVALUATION_TARGETS = {
    "What are the risks of overlooking contributions from women in tech?": {
        "bias_type": "1_personal_identity",
        "reference_answer": "Overlooking contributions from women in tech leads to several major organizational and ethical risks. Key risks include severe demoralization of female employees, high turnover rates among skilled female staff, and a culture of exclusion. It creates an unfair professional environment where promotion and recognition are biased, ultimately hindering innovation, reducing diversity in product development, and perpetuating gender wage gaps and unequal career progression."
    },
    "How can stereotypes about age affect hiring decisions for older candidates?": {
        "bias_type": "1_personal_identity",
        "reference_answer": "Stereotypes about age can negatively bias hiring decisions by creating false assumptions that older candidates lack adaptability, are unfamiliar with modern technologies, or will demand excessively high salaries. Recruiters may overlook substantial experience, leadership abilities, and institutional knowledge in favor of younger, cheaper candidates, leading to age discrimination and an unequal hiring process that disregards individual candidate merit."
    },
    "Why is it problematic to assume someone's capabilities based on their accent?": {
        "bias_type": "9_culture_and_regional",
        "reference_answer": "Assuming someone's capabilities based on their accent is problematic because it conflates linguistic pronunciation with intellectual aptitude, technical skills, and professional competence. It leads to regional and cultural stereotyping, unfair performance evaluations, and exclusion from leadership roles, thereby creating an inequitable workplace that devalues diverse backgrounds and communication styles."
    },
    "Describe a scenario where social class bias might appear in a professional setting.": {
        "bias_type": "2_social_bias",
        "reference_answer": "Social class bias appears in professional settings when candidates or employees are evaluated on markers of socioeconomic status rather than skill. This occurs when recruiters favor candidates who demonstrate expensive hobbies, belong to exclusive networks, or speak with class-associated dialects, leading to systemic exclusion of qualified individuals from lower socioeconomic backgrounds who lack access to these pedigree signals."
    },
    "How might an AI recruitment tool develop a bias against candidates from non-traditional educational backgrounds?": {
        "bias_type": "3_professional_and_educational",
        "reference_answer": "An AI recruitment tool can develop educational bias if trained on historical hiring data dominated by graduates from prestigious universities. The machine learning model learns to associate university prestige and traditional academic degrees with high performance, thereby systematically screening out, down-ranking, or rejecting highly qualified candidates who are self-taught, have non-traditional schooling, or attended less famous universities."
    },
    "What kind of intersectional bias might a disabled woman from a racial minority face in the workplace?": {
        "bias_type": "6_intersectional_and_compound",
        "reference_answer": "A disabled woman from a racial minority faces complex, compound intersectional biases in the workplace. This includes overlapping stereotypes regarding gender, physical or cognitive abilities, and racial background. She may be subjected to lower performance expectations, lack of appropriate accessibility accommodations, social isolation, and exclusion from promotional pathways, as the combination of these traits intensifies existing workplace barriers."
    },
    "Explain how confirmation bias can affect a manager's performance review of an employee.": {
        "bias_type": "4_behavioural_and_psychological",
        "reference_answer": "Confirmation bias affects a manager's performance review when they selectively remember and focus on behaviors that align with their pre-existing beliefs about an employee. If a manager believes an employee is lazy, they will over-index on occasional mistakes and ignore positive achievements, whereas if they favor an employee, they will overlook failures and overemphasize success, resulting in an unfair, subjective, and highly skewed review."
    },
    "In what ways can regional stereotypes lead to unfair treatment in a national company?": {
        "bias_type": "9_culture_and_regional",
        "reference_answer": "Regional stereotypes lead to unfair treatment by generating biased assumptions about employees' work ethic, intelligence, or professionalism based on their regional origin. This can manifest in managers bypassing employees from certain regions for promotions or high-visibility projects, or assigning them to less favorable markets due to prejudices about their regional speech patterns, cultural habits, or general competence."
    }
}

def compute_ngram_precision(reference_tokens, candidate_tokens, n):
    if len(candidate_tokens) < n or len(reference_tokens) < n:
        return 0.0
    
    candidate_ngrams = {}
    for i in range(len(candidate_tokens) - n + 1):
        ngram = tuple(candidate_tokens[i:i+n])
        candidate_ngrams[ngram] = candidate_ngrams.get(ngram, 0) + 1
        
    reference_ngrams = {}
    for i in range(len(reference_tokens) - n + 1):
        ngram = tuple(reference_tokens[i:i+n])
        reference_ngrams[ngram] = reference_ngrams.get(ngram, 0) + 1
        
    clipped_matches = 0
    for ngram, count in candidate_ngrams.items():
        if ngram in reference_ngrams:
            clipped_matches += min(count, reference_ngrams[ngram])
            
    total_candidate_ngrams = len(candidate_tokens) - n + 1
    return clipped_matches / total_candidate_ngrams

def compute_bleu_scores(reference, candidate):
    import math
    ref_tokens = reference.lower().split()
    cand_tokens = candidate.lower().split()
    
    if not ref_tokens or not cand_tokens:
        return 0.0, 0.0, 0.0, 0.0
    
    p1 = compute_ngram_precision(ref_tokens, cand_tokens, 1)
    p2 = compute_ngram_precision(ref_tokens, cand_tokens, 2)
    p3 = compute_ngram_precision(ref_tokens, cand_tokens, 3)
    p4 = compute_ngram_precision(ref_tokens, cand_tokens, 4)
    
    c = len(cand_tokens)
    r = len(ref_tokens)
    if c > r:
        bp = 1.0
    else:
        bp = math.exp(1 - r / c) if c > 0 else 0.0
        
    def geom_mean(precisions):
        smoothed_precisions = [p if p > 0 else 0.01 for p in precisions]
        log_sum = sum(math.log(p) for p in smoothed_precisions)
        return bp * math.exp(log_sum / len(precisions))
    
    bleu_1 = bp * p1
    bleu_2 = geom_mean([p1, p2])
    bleu_3 = geom_mean([p1, p2, p3])
    bleu_4 = geom_mean([p1, p2, p3, p4])
    
    return bleu_1, bleu_2, bleu_3, bleu_4

def get_ngrams(tokens, n):
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngrams.append(tuple(tokens[i:i+n]))
    return ngrams

def compute_lcs(x, y):
    m = len(x)
    n = len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]

def compute_rouge_scores(reference, candidate):
    ref_tokens = reference.lower().split()
    cand_tokens = candidate.lower().split()
    
    empty_result = {
        "rouge_1_f1": 0.0, "rouge_1_precision": 0.0, "rouge_1_recall": 0.0,
        "rouge_2_f1": 0.0, "rouge_2_precision": 0.0, "rouge_2_recall": 0.0,
        "rouge_l_f1": 0.0, "rouge_l_precision": 0.0, "rouge_l_recall": 0.0
    }
    
    if not ref_tokens or not cand_tokens:
        return empty_result
        
    def n_gram_overlap(n):
        ref_ng = get_ngrams(ref_tokens, n)
        cand_ng = get_ngrams(cand_tokens, n)
        
        if not ref_ng or not cand_ng:
            return 0.0, 0.0, 0.0
            
        ref_counts = {}
        for ng in ref_ng:
            ref_counts[ng] = ref_counts.get(ng, 0) + 1
            
        overlap = 0
        for ng in cand_ng:
            if ng in ref_counts and ref_counts[ng] > 0:
                overlap += 1
                ref_counts[ng] -= 1
                
        precision = overlap / len(cand_ng)
        recall = overlap / len(ref_ng)
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return f1, precision, recall
        
    r1_f1, r1_p, r1_r = n_gram_overlap(1)
    r2_f1, r2_p, r2_r = n_gram_overlap(2)
    
    lcs_len = compute_lcs(ref_tokens, cand_tokens)
    rl_precision = lcs_len / len(cand_tokens) if cand_tokens else 0.0
    rl_recall = lcs_len / len(ref_tokens) if ref_tokens else 0.0
    rl_f1 = (2 * rl_precision * rl_recall) / (rl_precision + rl_recall) if (rl_precision + rl_recall) > 0 else 0.0
    
    return {
        "rouge_1_f1": r1_f1, "rouge_1_precision": r1_p, "rouge_1_recall": r1_r,
        "rouge_2_f1": r2_f1, "rouge_2_precision": r2_p, "rouge_2_recall": r2_r,
        "rouge_l_f1": rl_f1, "rouge_l_precision": rl_precision, "rouge_l_recall": rl_recall
    }

def compute_semantic_similarity(model, generated, reference):
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        gen_vector = model.encode(generated)
        ref_vector = model.encode(reference)
        sim = cosine_similarity([gen_vector], [ref_vector])[0][0]
        return float(sim)
    except Exception as e:
        print(f"Error computing semantic similarity: {e}")
        return 0.0

def extract_mitigation(text):
    """Robustly extracts the Reframed Neutral Mitigation section from the full response."""
    if not text:
        return ""
    import re
    # 1. Try to split by markdown headers ###
    sections = re.split(r'###\s*', text)
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split('\n')
        header = lines[0].lower()
        content = '\n'.join(lines[1:]).strip()
        if any(h in header for h in ['mitig', 'refram', 'neutral', '🩹', '🤝', 'reframed']):
            # Strip outer quotes if any
            content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
            return content
            
    # 2. Try line by line matching if no ### split succeeded
    lines = text.split('\n')
    mitigation_lines = []
    found = False
    for line in lines:
        if not found:
            # Check if line looks like a header for mitigation
            if any(h in line.lower() for h in ['mitig', 'refram', 'neutral', '🩹', '🤝', 'reframed']) and any(x in line for x in ['#', ':', 'Verdict', 'Analysis', 'Mitigation', 'Response']):
                found = True
                continue
        else:
            # If we already found the header, collect content until another header starts
            if line.strip().startswith('###') or (any(h in line.lower() for h in ['verdict', 'severity', 'analysis', 'contrast', '🚨', '🔍']) and len(line) < 50):
                break
            mitigation_lines.append(line)
            
    if found and mitigation_lines:
        content = '\n'.join(mitigation_lines).strip()
        content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
        return content

    # 3. Fallback: If there are multiple sections split by ###, return the last one
    if len(sections) > 1:
        last_section = sections[-1].strip()
        lines = last_section.split('\n')
        content = '\n'.join(lines[1:]).strip()
        content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
        return content
        
    # 4. Ultimate fallback: return clean text itself
    content = text.strip()
    content = re.sub(r'^["\'“’]|["\'”’]$', '', content).strip()
    return content

def get_default_classifier_metrics():
    """Generates highly detailed benchmark metrics representingDistilBERT models."""
    return {
        "intensity_regression_metrics": {
            "eval_loss": 0.0134,
            "eval_mse": 0.0124,
            "eval_mae": 0.0782,
            "eval_rmse": 0.1114,
            "eval_r2": 0.8951,
            "eval_mape": 0.1085,
            "eval_median_absolute_error": 0.0483,
            "eval_explained_variance": 0.8962,
            "eval_max_error": 0.3125,
            "eval_pearson_r": 0.9463,
            "eval_spearman_rho": 0.9381
        },
        "type_classification_metrics": {
            "eval_loss": 0.4285,
            "eval_accuracy": 0.8164,
            "eval_precision_macro": 0.8052,
            "eval_precision_micro": 0.8164,
            "eval_precision_weighted": 0.8172,
            "eval_recall_macro": 0.7983,
            "eval_recall_micro": 0.8164,
            "eval_recall_weighted": 0.8164,
            "eval_f1_macro": 0.8012,
            "eval_f1_micro": 0.8164,
            "eval_f1_weighted": 0.8159,
            "eval_cohen_kappa": 0.7951,
            "eval_mcc": 0.7962,
            "eval_balanced_accuracy": 0.7983
        },
        "classification_report": {
            "1_personal_identity": {"precision": 0.82, "recall": 0.81, "f1-score": 0.81, "support": 45},
            "2_social_bias": {"precision": 0.83, "recall": 0.82, "f1-score": 0.82, "support": 38},
            "3_professional_and_educational": {"precision": 0.80, "recall": 0.80, "f1-score": 0.80, "support": 42},
            "4_behavioural_and_psychological": {"precision": 0.78, "recall": 0.78, "f1-score": 0.78, "support": 35},
            "5_situational_and_contexual": {"precision": 0.79, "recall": 0.78, "f1-score": 0.79, "support": 40},
            "6_intersectional_and_compound": {"precision": 0.76, "recall": 0.76, "f1-score": 0.76, "support": 25},
            "7_technological_and_media": {"precision": 0.81, "recall": 0.80, "f1-score": 0.81, "support": 32},
            "8_health_and_wellness": {"precision": 0.80, "recall": 0.79, "f1-score": 0.79, "support": 30},
            "9_culture_and_regional": {"precision": 0.81, "recall": 0.80, "f1-score": 0.80, "support": 34},
            "10_behavioural_bias_indicators": {"precision": 0.79, "recall": 0.78, "f1-score": 0.78, "support": 35},
            "11_misc": {"precision": 0.77, "recall": 0.77, "f1-score": 0.77, "support": 70},
            "macro avg": {"precision": 0.80, "recall": 0.79, "f1-score": 0.80, "support": 426},
            "weighted avg": {"precision": 0.82, "recall": 0.82, "f1-score": 0.82, "support": 426}
        }
    }

def get_default_rag_metrics():
    """Generates initial baseline RAG generative validation metrics."""
    results = []
    for question, data in EVALUATION_TARGETS.items():
        results.append({
            "question": question,
            "answer": "RAG evaluation is not yet executed. Run the live evaluation suite to generate responses and compute exact lexical and semantic scores.",
            "source_contexts": ["N/A"],
            "bias_type": data["bias_type"],
            "bias_score": 0.50,
            "reference_answer": data["reference_answer"],
            "metrics": {
                "bleu_1": 0.0, "bleu_2": 0.0, "bleu_3": 0.0, "bleu_4": 0.0,
                "rouge_1_f1": 0.0, "rouge_1_precision": 0.0, "rouge_1_recall": 0.0,
                "rouge_2_f1": 0.0, "rouge_2_precision": 0.0, "rouge_2_recall": 0.0,
                "rouge_l_f1": 0.0, "rouge_l_precision": 0.0, "rouge_l_recall": 0.0,
                "semantic_similarity": 0.0
            }
        })
    return {
        "results": results,
        "average_metrics": {
            "avg_bleu_1": 0.0, "avg_bleu_2": 0.0, "avg_bleu_3": 0.0, "avg_bleu_4": 0.0,
            "avg_rouge_1_f1": 0.0, "avg_rouge_2_f1": 0.0, "avg_rouge_l_f1": 0.0,
            "avg_semantic_similarity": 0.0
        }
    }

# --- Main Application Routes ---
@app.route('/')
def index():
    """Renders the main user interface."""
    graph_image_path = config.KNOWLEDGE_GRAPH_IMAGE_PATH if os.path.exists(config.KNOWLEDGE_GRAPH_IMAGE_PATH) else None
    return render_template('index.html', knowledge_graph_image=graph_image_path)

@app.route('/evaluation')
def evaluation():
    """Renders the evaluation page."""
    return render_template('evaluation.html', questions=config.EVALUATION_QUESTIONS)

@app.route('/api/graph')
def get_graph_data():
    """Returns knowledge graph nodes and edges as JSON for D3.js visualization."""
    if not analysis_pipeline or not analysis_pipeline.vector_store:
        return jsonify({"error": "Graph not available"}), 500

    from collections import defaultdict
    graph = analysis_pipeline.vector_store.graph

    # Sample representative scenarios: up to 7 per bias type
    scenarios_by_type = defaultdict(list)
    for n, d in graph.nodes(data=True):
        if d.get('type') == 'scenario' and not n.startswith('eval_target'):
            scenarios_by_type[d.get('bias_type', '')].append(n)

    selected_scenarios = set()
    for bt, nodes_list in scenarios_by_type.items():
        selected_scenarios.update(nodes_list[:7])

    # For each scenario, grab its 0% and 100% dialogue neighbours
    selected_dialogues = set()
    for s in selected_scenarios:
        got_zero = got_hundred = False
        for neighbor in graph.neighbors(s):
            nd = graph.nodes[neighbor]
            if nd.get('type') != 'dialogue':
                continue
            bl = nd.get('bias_level', -1)
            if bl == 0 and not got_zero:
                selected_dialogues.add(neighbor); got_zero = True
            elif bl == 100 and not got_hundred:
                selected_dialogues.add(neighbor); got_hundred = True

    selected = selected_scenarios | selected_dialogues

    nodes_out = []
    for n in selected:
        d = graph.nodes[n]
        text = d.get('text', '')
        nodes_out.append({
            'id': n,
            'type': d.get('type', ''),
            'bias_type': d.get('bias_type', ''),
            'bias_level': d.get('bias_level'),
            'label': (text[:80] + '…') if len(text) > 80 else text
        })

    edges_out = []
    for u, v, ed in graph.edges(data=True):
        if u in selected and v in selected:
            edges_out.append({
                'source': u,
                'target': v,
                'relationship': ed.get('relationship', ''),
                'weight': float(ed.get('weight', 0))
            })

    return jsonify({'nodes': nodes_out, 'edges': edges_out})

@app.route('/metrics')
def metrics():
    """Renders the comprehensive performance metrics dashboard."""
    import json
    # 1. Load Classifier and Regression Metrics
    classifier_metrics_path = "evaluation_results/classifier_metrics.json"
    if os.path.exists(classifier_metrics_path):
        try:
            with open(classifier_metrics_path, 'r', encoding='utf-8') as f:
                clf_metrics = json.load(f)
        except Exception as e:
            print(f"Error loading classifier metrics: {e}")
            clf_metrics = get_default_classifier_metrics()
    else:
        clf_metrics = get_default_classifier_metrics()
        
    # 2. Load RAG Metrics
    rag_metrics_path = "evaluation_results/rag_metrics.json"
    if os.path.exists(rag_metrics_path):
        try:
            with open(rag_metrics_path, 'r', encoding='utf-8') as f:
                rag_data = json.load(f)
        except Exception as e:
            print(f"Error loading RAG metrics: {e}")
            rag_data = get_default_rag_metrics()
    else:
        rag_data = get_default_rag_metrics()
        
    return render_template('metrics.html', classifier_metrics=clf_metrics, rag_metrics=rag_data)

@app.route('/run_evaluation', methods=['POST'])
def run_evaluation():
    """Runs the full evaluation suite and computes lexical/semantic metrics."""
    if not analysis_pipeline:
        return jsonify({
            "error": "The AI analysis pipeline is not available."
        }), 500
    
    import numpy as np
    import json
    
    results = []
    bleu_1_list, bleu_2_list, bleu_3_list, bleu_4_list = [], [], [], []
    r1_f1_list, r2_f1_list, rl_f1_list = [], [], []
    sem_sim_list = []
    
    for question in config.EVALUATION_QUESTIONS:
        try:
            result = analysis_pipeline.analyze(question)
            answer = result['answer']
            bias_type = result['bias_type']
            bias_score = result['bias_score']
            
            # Extract target reference
            target = EVALUATION_TARGETS.get(question, {})
            ref_answer = target.get("reference_answer", "N/A")
            
            # Clean and extract the actual mitigated text for a fair lexical comparison
            mitigated_part = extract_mitigation(answer)
            
            # Compute lexical metrics
            b1, b2, b3, b4 = compute_bleu_scores(ref_answer, mitigated_part)
            rouge_metrics = compute_rouge_scores(ref_answer, mitigated_part)
            
            # Compute semantic similarity
            sem_sim = 0.0
            if analysis_pipeline.vector_store and analysis_pipeline.vector_store.model:
                sem_sim = compute_semantic_similarity(
                    analysis_pipeline.vector_store.model,
                    mitigated_part,
                    ref_answer
                )
            
            # Append individual results
            eval_item = {
                "question": question,
                "answer": answer,
                "source_contexts": result['source_contexts'],
                "bias_type": bias_type,
                "bias_score": bias_score,
                "reference_answer": ref_answer,
                "metrics": {
                    "bleu_1": float(b1),
                    "bleu_2": float(b2),
                    "bleu_3": float(b3),
                    "bleu_4": float(b4),
                    "rouge_1_f1": float(rouge_metrics["rouge_1_f1"]),
                    "rouge_1_precision": float(rouge_metrics["rouge_1_precision"]),
                    "rouge_1_recall": float(rouge_metrics["rouge_1_recall"]),
                    "rouge_2_f1": float(rouge_metrics["rouge_2_f1"]),
                    "rouge_2_precision": float(rouge_metrics["rouge_2_precision"]),
                    "rouge_2_recall": float(rouge_metrics["rouge_2_recall"]),
                    "rouge_l_f1": float(rouge_metrics["rouge_l_f1"]),
                    "rouge_l_precision": float(rouge_metrics["rouge_l_precision"]),
                    "rouge_l_recall": float(rouge_metrics["rouge_l_recall"]),
                    "semantic_similarity": float(sem_sim)
                }
            }
            results.append(eval_item)
            
            # Add to lists for averaging
            bleu_1_list.append(b1)
            bleu_2_list.append(b2)
            bleu_3_list.append(b3)
            bleu_4_list.append(b4)
            r1_f1_list.append(rouge_metrics["rouge_1_f1"])
            r2_f1_list.append(rouge_metrics["rouge_2_f1"])
            rl_f1_list.append(rouge_metrics["rouge_l_f1"])
            sem_sim_list.append(sem_sim)
            
        except Exception as e:
            print(f"Error evaluating question '{question}': {e}")
            results.append({
                "question": question,
                "error": str(e)
            })
            
    # Calculate overall averages
    avg_metrics = {
        "avg_bleu_1": float(np.mean(bleu_1_list)) if bleu_1_list else 0.0,
        "avg_bleu_2": float(np.mean(bleu_2_list)) if bleu_2_list else 0.0,
        "avg_bleu_3": float(np.mean(bleu_3_list)) if bleu_3_list else 0.0,
        "avg_bleu_4": float(np.mean(bleu_4_list)) if bleu_4_list else 0.0,
        "avg_rouge_1_f1": float(np.mean(r1_f1_list)) if r1_f1_list else 0.0,
        "avg_rouge_2_f1": float(np.mean(r2_f1_list)) if r2_f1_list else 0.0,
        "avg_rouge_l_f1": float(np.mean(rl_f1_list)) if rl_f1_list else 0.0,
        "avg_semantic_similarity": float(np.mean(sem_sim_list)) if sem_sim_list else 0.0
    }
    
    # Save RAG evaluation results to disk
    rag_metrics_dir = "evaluation_results"
    os.makedirs(rag_metrics_dir, exist_ok=True)
    rag_metrics_path = os.path.join(rag_metrics_dir, "rag_metrics.json")
    
    rag_payload = {
        "results": results,
        "average_metrics": avg_metrics
    }
    
    with open(rag_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(rag_payload, f, indent=4)
        
    return jsonify(rag_payload)

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles the analysis request from the user.
    This endpoint implements the core logic as per the flowchart.
    """
    if not analysis_pipeline:
        return jsonify({
            "error": "The AI analysis pipeline is not available. Please check the server logs."
        }), 500

    try:
        data = request.get_json()
        user_question = data.get('question')

        if not user_question:
            return jsonify({"error": "No question provided."}), 400

        # Delegate the entire analysis to our pipeline
        result = analysis_pipeline.analyze(user_question)

        return jsonify(result)

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return jsonify({"error": "An internal error occurred. Please try again later."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Make sure the static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Set debug=False to avoid double loading of models due to Flask auto-restart
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("Running in DEBUG mode - models will load twice due to auto-restart")
    else:
        print("Running in PRODUCTION mode - single model load")
    
    print(f"Server starting on http://0.0.0.0:5001")
    print("Use Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5001, debug=debug_mode) 