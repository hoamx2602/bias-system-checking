import os
import config  # loads .env and configures HF environment variables

import json
import warnings
import shutil
import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments, EarlyStoppingCallback
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score, median_absolute_error, explained_variance_score,
    accuracy_score, precision_score, recall_score, f1_score, cohen_kappa_score, matthews_corrcoef, balanced_accuracy_score,
    classification_report
)

# Suppress common warnings
warnings.filterwarnings("ignore", message=".*symlinks.")
warnings.filterwarnings("ignore", message=".*pin_memory.*")
warnings.filterwarnings("ignore", message=".*Xet Storage.*")

os.environ["HF_HUB_OFFLINE"] = "1"  # Use cached models only during training

class WeightedTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if class_weights is not None:
            self.class_weights = torch.tensor(class_weights, dtype=torch.float).to(self.args.device)
        else:
            self.class_weights = None

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        if self.class_weights is not None and labels is not None:
            import torch.nn as nn
            loss_fct = nn.CrossEntropyLoss(weight=self.class_weights)
            loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        else:
            loss = outputs.get("loss") if isinstance(outputs, dict) else outputs[0]
        return (loss, outputs) if return_outputs else loss

# --- Bias Type Mapping ---
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

# --- Data Parsing Utilities ---
def parse_bias_percentage(version_string):
    """
    Parse bias percentage from version string with multiple format support.
    """
    import re
    
    # Try to extract percentage from parentheses
    percentage_match = re.search(r'\((\d+)%\)', version_string)
    if percentage_match:
        return int(percentage_match.group(1))
    
    # If it's a "Mixed Bias" version, assign 50% (moderate bias)
    if "Mixed Bias" in version_string:
        return 50
    
    # If it contains "No Bias", assign 0%
    if "No Bias" in version_string:
        return 0
    
    # If it contains "Extreme" or high-level bias indicators, assign 100%
    if any(indicator in version_string.lower() for indicator in ["extreme", "severe", "high"]):
        return 100
    
    # For any other format, default to moderate bias (50%)
    return 50

# --- Dataset Class ---
class BiasMultiDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512, is_regression=True):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.is_regression = is_regression
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        inputs = {k: v.squeeze(0) for k, v in inputs.items()}
        if self.is_regression:
            inputs["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
        else:
            inputs["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return inputs

# --- Data Loading ---
def load_bias_data(data_dir=config.DATA_DIR, sample_ratio=config.TRAIN_SAMPLE_RATIO):
    """Load and preprocess data from all bias dataset files, returning texts, regression labels, and classification labels."""
    all_texts = []
    all_intensity_labels = []
    all_type_labels = []
    
    print(f"Loading data from {data_dir}...")
    for filename in os.listdir(data_dir):
        if filename.startswith("bias_data_for_type_") and filename.endswith(".json"):
            # Extract bias type name
            bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]
            type_label = BIAS_TYPE_MAPPING.get(bias_type, 10) # default to misc (label 10)
            
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for item in data:
                    for conversation in item["parameters"]["conversations"]:
                        version = conversation["version"]
                        dialogues = conversation["dialogues"]
                        
                        # Parse bias level with multiple format support
                        bias_percentage = parse_bias_percentage(version)
                        normalized_bias = bias_percentage / 100.0
                        
                        text = " ".join(dialogues)
                        all_texts.append(text)
                        all_intensity_labels.append(normalized_bias)
                        all_type_labels.append(type_label)
    
    if sample_ratio < 1.0:
        print(f"Sampling {sample_ratio * 100:.0f}% of the data...")
        sample_size = max(100, int(len(all_texts) * sample_ratio))
        indices = np.random.choice(len(all_texts), sample_size, replace=False)
        all_texts = [all_texts[i] for i in indices]
        all_intensity_labels = [all_intensity_labels[i] for i in indices]
        all_type_labels = [all_type_labels[i] for i in indices]
    
    print(f"Loaded {len(all_texts)} text samples.")
    return all_texts, all_intensity_labels, all_type_labels

# --- Metrics Computation ---
def compute_regression_metrics(eval_pred):
    """Compute exhaustive regression metrics."""
    predictions, labels = eval_pred
    predictions = predictions.squeeze()
    
    mse = mean_squared_error(labels, predictions)
    mae = mean_absolute_error(labels, predictions)
    rmse = np.sqrt(mse)
    r2 = r2_score(labels, predictions)
    
    # Avoid division by zero in MAPE
    epsilon = 1e-5
    mape = np.mean(np.abs((labels - predictions) / (labels + epsilon)))
    
    median_ae = median_absolute_error(labels, predictions)
    exp_var = explained_variance_score(labels, predictions)
    max_err = np.max(np.abs(labels - predictions))
    
    # Pearson and Spearman correlations
    try:
        from scipy.stats import pearsonr, spearmanr
        pearson_r, _ = pearsonr(predictions, labels)
        spearman_rho, _ = spearmanr(predictions, labels)
    except Exception:
        pearson_r, spearman_rho = 0.0, 0.0
        
    return {
        "mse": float(mse),
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "mape": float(mape),
        "median_absolute_error": float(median_ae),
        "explained_variance": float(exp_var),
        "max_error": float(max_err),
        "pearson_r": float(pearson_r),
        "spearman_rho": float(spearman_rho)
    }

def compute_classification_metrics(eval_pred):
    """Compute exhaustive classification metrics."""
    predictions, labels = eval_pred
    preds_flat = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, preds_flat)
    
    precision_macro = precision_score(labels, preds_flat, average="macro", zero_division=0)
    precision_micro = precision_score(labels, preds_flat, average="micro", zero_division=0)
    precision_weighted = precision_score(labels, preds_flat, average="weighted", zero_division=0)
    
    recall_macro = recall_score(labels, preds_flat, average="macro", zero_division=0)
    recall_micro = recall_score(labels, preds_flat, average="micro", zero_division=0)
    recall_weighted = recall_score(labels, preds_flat, average="weighted", zero_division=0)
    
    f1_macro = f1_score(labels, preds_flat, average="macro", zero_division=0)
    f1_micro = f1_score(labels, preds_flat, average="micro", zero_division=0)
    f1_weighted = f1_score(labels, preds_flat, average="weighted", zero_division=0)
    
    cohen_kappa = cohen_kappa_score(labels, preds_flat)
    mcc = matthews_corrcoef(labels, preds_flat)
    balanced_acc = balanced_accuracy_score(labels, preds_flat)
    
    return {
        "accuracy": float(accuracy),
        "precision_macro": float(precision_macro),
        "precision_micro": float(precision_micro),
        "precision_weighted": float(precision_weighted),
        "recall_macro": float(recall_macro),
        "recall_micro": float(recall_micro),
        "recall_weighted": float(recall_weighted),
        "f1_macro": float(f1_macro),
        "f1_micro": float(f1_micro),
        "f1_weighted": float(f1_weighted),
        "cohen_kappa": float(cohen_kappa),
        "mcc": float(mcc),
        "balanced_accuracy": float(balanced_acc)
    }

# --- Visualizing Confusion Matrix ---
def plot_and_save_confusion_matrix(labels, predictions, save_path):
    """Plot and save confusion matrix heatmap using matplotlib and seaborn."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.metrics import confusion_matrix
        
        cm = confusion_matrix(labels, predictions)
        plt.figure(figsize=(12, 10))
        
        class_names = [
            "Personal", "Social", "Prof & Edu", 
            "Behav & Psych", "Situational", "Intersect", 
            "Tech & Media", "Health & Well", "Culture & Reg", 
            "Behav Indicators", "Misc"
        ]
        
        # Plot heatmap
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.title("Confusion Matrix - Bias Type Classifier", fontsize=16)
        plt.ylabel("Actual Label", fontsize=12)
        plt.xlabel("Predicted Label", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"Confusion matrix plot successfully saved to {save_path}")
    except Exception as e:
        print(f"Skipping confusion matrix plot generation due to: {e}")

# --- Main Training Function ---
def main():
    """Main function to orchestrate the sequential dual training and validation metrics pipeline."""
    
    # --- 1. Load and Prepare Data ---
    print("--- Step 1: Loading and Preparing Data ---")
    texts, intensity_labels, type_labels = load_bias_data()
    
    # Split datasets
    train_texts, val_texts, train_int_labels, val_int_labels, train_type_labels, val_type_labels = train_test_split(
        texts, intensity_labels, type_labels, test_size=config.TEST_SPLIT_SIZE, random_state=42
    )
    
    # --- 2. Initialize Tokenizer ---
    print("\n--- Step 2: Initializing Tokenizer ---")
    cache_dir = os.environ.get("HF_HOME")
    model_kwargs = {"cache_dir": cache_dir}
    print(f"Models will be cached to: {cache_dir}")
    tokenizer = AutoTokenizer.from_pretrained(config.CLASSIFIER_MODEL, **model_kwargs)

    # Create datasets
    train_int_dataset = BiasMultiDataset(train_texts, train_int_labels, tokenizer, is_regression=True)
    val_int_dataset = BiasMultiDataset(val_texts, val_int_labels, tokenizer, is_regression=True)

    train_type_dataset = BiasMultiDataset(train_texts, train_type_labels, tokenizer, is_regression=False)
    val_type_dataset = BiasMultiDataset(val_texts, val_type_labels, tokenizer, is_regression=False)

    # Make output folders
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    os.makedirs(config.EVALUATION_RESULTS_DIR, exist_ok=True)

    # Setup hardware info — re-check at runtime in case torch was reinstalled since config loaded
    device_name = config.DEVICE
    if device_name == "cuda":
        print(f"Using Device: cuda ({torch.cuda.get_device_name(0)})")
    elif device_name == "mps":
        print("Using Device: mps (Apple Silicon Metal Performance Shaders)")
    else:
        print("Using Device: cpu  (WARNING: no GPU detected — training will be slow)")
        print("If you have a GPU, install CUDA-enabled PyTorch: pip install torch --index-url https://download.pytorch.org/whl/cu124")

    # =========================================================================
    # PART A: Train Bias Intensity Regressor
    # =========================================================================
    print("\n=======================================================")
    print("PART A: Training Bias Intensity Regressor")
    print("=======================================================")
    
    model_int = AutoModelForSequenceClassification.from_pretrained(
        config.CLASSIFIER_MODEL,
        num_labels=1,  # Regression
        **model_kwargs
    )
    if device_name != "cpu":
        model_int.to(device_name)

    training_args_int = TrainingArguments(
        output_dir=os.path.join(config.RESULTS_DIR, "intensity"),
        num_train_epochs=config.TRAIN_EPOCHS,
        learning_rate=config.LEARNING_RATE,
        per_device_train_batch_size=config.TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=config.EVAL_BATCH_SIZE,
        warmup_ratio=0.1,
        weight_decay=config.WEIGHT_DECAY,
        logging_dir=os.path.join(config.LOGS_DIR, "intensity"),
        logging_steps=config.LOGGING_STEPS,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="mse",
        greater_is_better=False,
        save_total_limit=1,
        fp16=(device_name == "cuda"),
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        dataloader_num_workers=2,
        report_to="none"
    )
    
    trainer_int = Trainer(
        model=model_int,
        args=training_args_int,
        train_dataset=train_int_dataset,
        eval_dataset=val_int_dataset,
        compute_metrics=compute_regression_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=5)]
    )
    
    print("Starting Bias Intensity model training...")
    trainer_int.train()
    print("Evaluating Bias Intensity model...")
    eval_results_int = trainer_int.evaluate()
    
    # Save Intensity Model
    if os.path.exists(config.TRAINED_MODEL_DIR_INTENSITY):
        shutil.rmtree(config.TRAINED_MODEL_DIR_INTENSITY, ignore_errors=True)
    print(f"Saving Bias Intensity Model to {config.TRAINED_MODEL_DIR_INTENSITY}...")
    trainer_int.save_model(config.TRAINED_MODEL_DIR_INTENSITY)
    tokenizer.save_pretrained(config.TRAINED_MODEL_DIR_INTENSITY)
    
    # =========================================================================
    # PART B: Train Bias Type Classifier (11 Classes)
    # =========================================================================
    print("\n=======================================================")
    print("PART B: Training Bias Type Classifier (11 Classes)")
    print("=======================================================")
    
    model_type = AutoModelForSequenceClassification.from_pretrained(
        config.CLASSIFIER_MODEL,
        num_labels=11,  # 11 Classes
        **model_kwargs
    )
    if device_name != "cpu":
        model_type.to(device_name)

    training_args_type = TrainingArguments(
        output_dir=os.path.join(config.RESULTS_DIR, "type"),
        num_train_epochs=config.TRAIN_EPOCHS,
        learning_rate=config.LEARNING_RATE,
        per_device_train_batch_size=config.TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=config.EVAL_BATCH_SIZE,
        warmup_ratio=0.1,
        weight_decay=config.WEIGHT_DECAY,
        logging_dir=os.path.join(config.LOGS_DIR, "type"),
        logging_steps=config.LOGGING_STEPS,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        save_total_limit=1,
        fp16=(device_name == "cuda"),
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        dataloader_num_workers=2,
        report_to="none"
    )
    
    # Compute balanced class weights to address severe class imbalance across the 11 classes
    from sklearn.utils.class_weight import compute_class_weight
    classes_list = np.array(range(11))
    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=classes_list,
        y=train_type_labels
    )
    print(f"Computed Class Weights for Type Classification: {class_weights}")
    
    trainer_type = WeightedTrainer(
        class_weights=class_weights,
        model=model_type,
        args=training_args_type,
        train_dataset=train_type_dataset,
        eval_dataset=val_type_dataset,
        compute_metrics=compute_classification_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=5)]
    )
    
    print("Starting Bias Type classification training...")
    trainer_type.train()
    print("Evaluating Bias Type model...")
    eval_results_type = trainer_type.evaluate()
    
    # Generate predictions on validation set for detailed classification report
    predictions_out = trainer_type.predict(val_type_dataset)
    pred_labels = np.argmax(predictions_out.predictions, axis=1)
    true_labels = predictions_out.label_ids
    
    # Save Type Model
    if os.path.exists(config.TRAINED_MODEL_DIR_TYPE):
        shutil.rmtree(config.TRAINED_MODEL_DIR_TYPE, ignore_errors=True)
    print(f"Saving Bias Type Model to {config.TRAINED_MODEL_DIR_TYPE}...")
    trainer_type.save_model(config.TRAINED_MODEL_DIR_TYPE)
    tokenizer.save_pretrained(config.TRAINED_MODEL_DIR_TYPE)
    
    # Plot and save confusion matrix image
    confusion_img_path = os.path.join("static", "confusion_matrix.png")
    plot_and_save_confusion_matrix(true_labels, pred_labels, confusion_img_path)

    # Save detailed classification report in validation box format
    class_names = [
        "1_personal_identity", "2_social_bias", "3_professional_and_educational", 
        "4_behavioural_and_psychological", "5_situational_and_contexual", "6_intersectional_and_compound", 
        "7_technological_and_media", "8_health_and_wellness", "9_culture_and_regional", 
        "10_behavioural_bias_indicators", "11_misc"
    ]
    report_dict = classification_report(true_labels, pred_labels, target_names=class_names, output_dict=True)
    report_text = classification_report(true_labels, pred_labels, target_names=class_names)
    print("\n--- Detailed Validation Classification Report ---")
    print(report_text)
    
    # Combine ALL metrics for output
    combined_metrics = {
        "intensity_regression_metrics": eval_results_int,
        "type_classification_metrics": eval_results_type,
        "classification_report": report_dict
    }
    
    metrics_json_path = os.path.join(config.EVALUATION_RESULTS_DIR, "classifier_metrics.json")
    with open(metrics_json_path, 'w', encoding='utf-8') as f:
        json.dump(combined_metrics, f, indent=4)
        
    print(f"\n✅ All and every validation metrics successfully outputted and saved in validation box at: {metrics_json_path}")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()