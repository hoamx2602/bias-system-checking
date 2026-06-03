import os
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification, TextIteratorStreamer
from threading import Thread
from vector_store import get_vector_store
import config
import configparser

# --- Bias Type and Display Mappings ---
BIAS_TYPE_MAPPING = {
    "1_personal_identity": 0,
    "2_social_bias": 1,
    "3_professional_and_educational": 2,
    "4_behavioural_and_psychological": 3,
    "5_situational_and_contexual": 4,
    "6_intersectional_and_compound": 5,
    "7_technological_and_media": 6,
    "8_health_and_wellness": 7,
    "9_culture_and_regional": 8,
    "10_behavioural_bias_indicators": 9,
    "11_misc": 10
}

REVERSE_BIAS_TYPE_MAPPING = {v: k for k, v in BIAS_TYPE_MAPPING.items()}

DISPLAY_BIAS_TYPES = {
    "1_personal_identity": "Personal Identity Bias",
    "2_social_bias": "Social Bias",
    "3_professional_and_educational": "Professional & Educational Bias",
    "4_behavioural_and_psychological": "Behavioural & Psychological Bias",
    "5_situational_and_contexual": "Situational & Contextual Bias",
    "6_intersectional_and_compound": "Intersectional & Compound Bias",
    "7_technological_and_media": "Technological & Media Bias",
    "8_health_and_wellness": "Health & Wellness Bias",
    "9_culture_and_regional": "Cultural & Regional Bias",
    "10_behavioural_bias_indicators": "Behavioural Bias Indicators",
    "11_misc": "Miscellaneous Bias",
    "N/A": "Neutral / Not Applicable"
}

DOUBLE_CONTRAST_PROMPT_TEMPLATE = """
You are an expert AI Bias and Ethics Analyst. You are analyzing a dialogue or scenario for potential bias.

We have run a supervised bias detection system on the input text:
- Predicted Bias Type: {bias_type_display}
- Predicted Bias Intensity: {bias_score:.1f}%

Here is the retrieved context scenario that represents this bias category:
---
{context}
---

To guide your analysis, here are reference examples from our bias knowledge base:
1. **Zero Bias Reference (0% Bias)** - An exemplary neutral and objective communication:
"{no_bias_example}"

2. **Extreme Bias Reference (100% Bias)** - A highly biased and problematic communication:
"{extreme_bias_example}"

Your task is to analyze the user's input dialogue/question and generate a structured ethical analysis and reframing.

User Input/Dialogue:
"{question}"

Please provide your response in the following strict markdown format:

### 🚨 Bias Verdict & Severity
[Provide a clear verdict on the presence, type, and severity of bias in the user's input, referencing the predicted {bias_score:.1f}% intensity. Keep this section very concise (maximum 2-3 sentences).]

### 🔍 Explanatory Analysis & Contrast
[Explain how the bias manifests in the user input. Contrast it against the Zero Bias Reference (0%) and Extreme Bias Reference (100%) provided above to show why it is classified this way. Keep this section very concise (maximum 3-4 sentences).]

### 🩹 Reframed Neutral Mitigation
[Provide a complete, revised, and 100% neutral/unbiased version of the dialogue or statement.
CRITICAL RULES FOR THIS SECTION:
1. PRESERVE THE ORIGINAL INTENT, ROLES, AND COMMUNICATION ACTION: You must keep the exact same professional context, actions, and roles of the original user input. Do NOT let the retrieved context scenarios or reference examples (like classroom presentations, patient-doctor consulting, etc.) bleed into or influence this mitigation unless the original user input was already in that setting. For example, if the user input is a recruitment rejection letter, this section must remain a clean, objective, professional recruitment rejection.
2. ZERO META-COMMENTARY OR EXPLANATIONS: Do NOT output any explanations, justifications, footnotes, reasons, or trailing "Explanation:" blocks in this section. Output ONLY the clean, reframed text inside quotation marks and nothing else.
3. If the user's input is a professional, ethical, or analytical question (e.g. "What are the risks...", "How can...", "Why is...", "Describe...", "Explain..."), do NOT just reframe the question. Instead, provide a highly detailed, comprehensive, objective, and unbiased answer that directly and exhaustively answers the question, detailing all key organizational, ethical, or systemic risks, factors, and consequences neutrally. Ensure this section is fully detailed and complete, matching a professional reference answer.]
"""

def get_hf_token():
    """Reads the Hugging Face token from config.ini"""
    parser = configparser.ConfigParser()
    parser.read('config.ini')
    token = parser.get('huggingface', 'token', fallback=None)
    if not token or "YOUR_HUGGING_FACE_TOKEN_HERE" in token:
        return None
    return token

class BiasAnalysisPipeline:
    """
    A hybrid pipeline that integrates supervised classification/regression models,
    vector store for context-filtered retrieval, and a generative LLM (Gemma 3)
    using Double-Contrast Prompting.
    """
    def __init__(self, vector_store):
        print("Initializing Bias Analysis Pipeline...")
        self.vector_store = vector_store
        
        # Determine the device to use
        self.device = "cuda" if config.USE_CUDA else "cpu"
        print(f"Using device: {self.device}")

        # Get auth token and set it as an environment variable
        auth_token = get_hf_token()
        if not auth_token:
            raise ValueError("Hugging Face token not found in config.ini. Please add it to continue.")
        os.environ["HUGGING_FACE_HUB_TOKEN"] = auth_token

        hf_cache = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
        local_kwargs = {"local_files_only": False}
        if hf_cache:
            local_kwargs["cache_dir"] = hf_cache
        
        load_kwargs = {}
        if self.device == "cuda":
            load_kwargs.update({"dtype": torch.float16, "device_map": "auto"})
        else:
            load_kwargs.update({"dtype": torch.float32, "device_map": {"": "cpu"}})

        # --- Load Supervised Bias Intensity Regressor ---
        if os.path.exists(config.TRAINED_MODEL_DIR_INTENSITY):
            print(f"Loading fine-tuned bias intensity model from {config.TRAINED_MODEL_DIR_INTENSITY}...")
            self.intensity_tokenizer = AutoTokenizer.from_pretrained(config.TRAINED_MODEL_DIR_INTENSITY, **local_kwargs)
            self.intensity_model = AutoModelForSequenceClassification.from_pretrained(config.TRAINED_MODEL_DIR_INTENSITY, **load_kwargs)
        else:
            print(f"Fine-tuned bias intensity model not found. Loading base fallback model...")
            self.intensity_tokenizer = AutoTokenizer.from_pretrained(config.CLASSIFIER_MODEL, **local_kwargs)
            self.intensity_model = AutoModelForSequenceClassification.from_pretrained(config.CLASSIFIER_MODEL, num_labels=1, **load_kwargs)
        self.intensity_model.to(self.device)
        self.intensity_model.eval()

        # --- Load Supervised Bias Type Classifier ---
        if os.path.exists(config.TRAINED_MODEL_DIR_TYPE):
            print(f"Loading fine-tuned bias type model from {config.TRAINED_MODEL_DIR_TYPE}...")
            self.type_tokenizer = AutoTokenizer.from_pretrained(config.TRAINED_MODEL_DIR_TYPE, **local_kwargs)
            self.type_model = AutoModelForSequenceClassification.from_pretrained(config.TRAINED_MODEL_DIR_TYPE, **load_kwargs)
        else:
            print(f"Fine-tuned bias type model not found. Loading base fallback model...")
            self.type_tokenizer = AutoTokenizer.from_pretrained(config.CLASSIFIER_MODEL, **local_kwargs)
            self.type_model = AutoModelForSequenceClassification.from_pretrained(config.CLASSIFIER_MODEL, num_labels=11, **load_kwargs)
        self.type_model.to(self.device)
        self.type_model.eval()

        # --- Load Generative Model (Gemma 3) ---
        print(f"Loading generative model: {config.GENERATIVE_MODEL}...")
        self.tokenizer = AutoTokenizer.from_pretrained(config.GENERATIVE_MODEL, **local_kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.GENERATIVE_MODEL,
            **load_kwargs,
            **local_kwargs,
        )

        # Set pad token if it's not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model.eval() # Set model to evaluation mode
        print("All models loaded successfully.")

    def predict_bias(self, text):
        """Predicts bias intensity (0.0 to 1.0) and bias type string."""
        # Predict Intensity
        inputs_int = self.intensity_tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs_int = self.intensity_model(**inputs_int)
            intensity = outputs_int.logits.squeeze().item()
            # Clip between 0.0 and 1.0
            predicted_intensity = max(0.0, min(1.0, float(intensity)))
            
        # Predict Type
        inputs_type = self.type_tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs_type = self.type_model(**inputs_type)
            pred_idx = torch.argmax(outputs_type.logits, dim=1).item()
            predicted_type_str = REVERSE_BIAS_TYPE_MAPPING.get(pred_idx, "11_misc")
            
        return predicted_intensity, predicted_type_str

    def analyze(self, user_question):
        """
        Analyzes user text via supervised classifier-RAG ensemble flow.
        1. Predict text bias score and type.
        2. Retrieve similar scenario context filtered by the predicted type.
        3. Query knowledge graph for extreme contrast references (0% and 100%).
        4. Generate structured ethical explanation and neutral reframing via Gemma 3.
        """
        print(f"Analyzing question: '{user_question}'")
        
        # --- Step 1: Supervised Prediction ---
        print("Step 1: Running supervised bias classifiers...")
        predicted_intensity, predicted_type_str = self.predict_bias(user_question)
        bias_type_display = DISPLAY_BIAS_TYPES.get(predicted_type_str, "Miscellaneous Bias")
        print(f"-> Predicted Bias Intensity: {predicted_intensity*100:.1f}%, Type: {predicted_type_str} ({bias_type_display})")
        
        # --- Step 2: Retrieve Context with Category Filtering ---
        print("Step 2: Retrieving category-filtered context from vector store...")
        retrieved_results = self.vector_store.search(user_question, top_k=3, bias_type=predicted_type_str)
        
        if not retrieved_results:
            # Fallback to unfiltered search
            print("No filtered context found. Falling back to unfiltered search...")
            retrieved_results = self.vector_store.search(user_question, top_k=3)
            
        if not retrieved_results:
            print("No context found in vector store.")
            return {
                "answer": "I could not find a relevant context in my knowledge base. The input appears to be neutral.",
                "source_contexts": ["No context found."],
                "bias_type": predicted_type_str,
                "bias_type_display": bias_type_display,
                "bias_score": predicted_intensity,
                "no_bias_example": "N/A",
                "extreme_bias_example": "N/A"
            }
            
        # Combine the text from the top results to form the context
        source_contexts = [result['text'] for result in retrieved_results]
        combined_context = "\n\n---\n\n".join(source_contexts)

        # --- Step 3: Double-Contrast Retrieval ---
        print("Step 3: Querying knowledge graph for contrastive references...")
        no_bias_example = ""
        extreme_bias_example = ""
        
        graph = self.vector_store.graph
        
        # Try to find dialogues connected to the top scenario
        top_scenario_key = retrieved_results[0]['key']
        if top_scenario_key in graph:
            for neighbor in graph.neighbors(top_scenario_key):
                node_data = graph.nodes[neighbor]
                if node_data.get("type") == "dialogue":
                    bias_level = node_data.get("bias_level")
                    if bias_level == 0:
                        no_bias_example = node_data.get("text", "")
                    elif bias_level == 100:
                        extreme_bias_example = node_data.get("text", "")
                        
        # First fallback: check other retrieved scenarios
        if not no_bias_example or not extreme_bias_example:
            for res in retrieved_results:
                scen_key = res['key']
                if scen_key in graph:
                    for neighbor in graph.neighbors(scen_key):
                        node_data = graph.nodes[neighbor]
                        if node_data.get("type") == "dialogue":
                            bias_level = node_data.get("bias_level")
                            if not no_bias_example and bias_level == 0:
                                no_bias_example = node_data.get("text", "")
                            if not extreme_bias_example and bias_level == 100:
                                extreme_bias_example = node_data.get("text", "")
                                
        # Ultimate fallback: search across the entire graph for the predicted bias type
        if not no_bias_example or not extreme_bias_example:
            for node, node_data in graph.nodes(data=True):
                if node_data.get("type") == "dialogue" and node_data.get("bias_type") == predicted_type_str:
                    bias_level = node_data.get("bias_level")
                    if not no_bias_example and bias_level == 0:
                        no_bias_example = node_data.get("text", "")
                    if not extreme_bias_example and bias_level == 100:
                        extreme_bias_example = node_data.get("text", "")
                        
        # Last-ditch defaults if dataset lacks specific classes
        if not no_bias_example:
            no_bias_example = "Let's discuss qualifications and experience objectively."
        if not extreme_bias_example:
            extreme_bias_example = "This person is completely unsuitable based purely on personal traits!"

        # --- Step 4: Construct Prompt and Generate Mitigation ---
        print("Step 4: Constructing double-contrast prompt and generating answer...")
        user_prompt = DOUBLE_CONTRAST_PROMPT_TEMPLATE.format(
            bias_type_display=bias_type_display,
            bias_score=predicted_intensity * 100.0,
            context=combined_context,
            no_bias_example=no_bias_example,
            extreme_bias_example=extreme_bias_example,
            question=user_question
        )
        
        messages = [
            {"role": "system", "content": "You are a professional AI Bias and Ethics Analyst. Follow the requested structured markdown format and base your answer on the provided context and references."},
            {"role": "user", "content": user_prompt},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=800,
            do_sample=True,
            temperature=0.4,
            top_p=0.9,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3
        )
        
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        generated_text = ""
        print("\n--- Streaming Analyst's Answer ---")
        for new_text in streamer:
            generated_text += new_text
            print(new_text, end="", flush=True)
        print("\n----------------------------------\n")
        
        thread.join()
        print("Answer generated successfully.")

        return {
            "answer": generated_text,
            "source_contexts": source_contexts,
            "bias_type": predicted_type_str,
            "bias_type_display": bias_type_display,
            "bias_score": float(predicted_intensity),
            "no_bias_example": no_bias_example,
            "extreme_bias_example": extreme_bias_example
        }

# --- Singleton instance ---
# This ensures that the models and vector store are loaded only once.
_pipeline = None

def get_analysis_pipeline(force_rebuild_store=False):
    """
    Initializes and returns a singleton instance of the BiasAnalysisPipeline.
    """
    global _pipeline
    if _pipeline is None:
        # First, get the vector store (build it if it doesn't exist)
        vector_store = get_vector_store(force_rebuild=force_rebuild_store)
        
        # Then, initialize the pipeline with the store
        _pipeline = BiasAnalysisPipeline(vector_store=vector_store)
        
    return _pipeline

if __name__ == '__main__':
    # Example usage of the pipeline
    print("--- Running standalone example ---")
    pipeline = get_analysis_pipeline()
    
    # Example question
    test_question = "What are the risks of overlooking contributions from women in tech?"
    
    # Analyze the question
    result = pipeline.analyze(test_question)
    
    # Print the results
    print("\n--- Analysis Result ---")
    print(f"Question: {test_question}")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nSource Contexts: {result['source_contexts']}")
    print(f"Detected Bias Type: {result['bias_type']}")
    print("-------------------------") 