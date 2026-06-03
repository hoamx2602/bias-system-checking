"""
Preprocess the bias dataset and create vector embeddings

This script loads the bias dataset, creates embeddings using SentenceTransformers,
and saves the vector store for faster loading in the main application.
"""

import os
import json
import time
import argparse
from tqdm import tqdm
import config

def build_knowledge_assets():
    """
    Builds all necessary knowledge assets, including the vector store
    and the knowledge graph visualization.
    """
    print("--- Starting Knowledge Asset Building Process ---")
    start_time = time.time()

    # --- 1. Check if assets already exist ---
    if os.path.exists(config.VECTOR_STORE_PATH):
        try:
            response = input(f"Vector store already exists at '{config.VECTOR_STORE_PATH}'. Rebuild it? [y/N]: ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ("y", "yes"):
            print("Skipping rebuild. Using existing assets.")
            return

    print("Building new vector store from data...")
    
    # --- 2. Create and Populate Vector Store ---
    # Lazy import to avoid heavy dependencies unless we actually rebuild
    from vector_store import BiasVectorStore
    # Enable accelerated HF downloads if available
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
    vector_store = BiasVectorStore()
    
    print(f"Loading data from '{config.DATA_DIR}' directory...")
    vector_store.load_data(config.DATA_DIR)
    
    # --- 3. Save Vector Store ---
    print(f"Saving vector store to '{config.VECTOR_STORE_PATH}'...")
    vector_store.save()
    
    # --- 4. Generate and Save Knowledge Graph Visualization ---
    print("Generating knowledge graph visualization...")
    if not os.path.exists("static"):
        os.makedirs("static")
    
    graph_path = vector_store.visualize_graph(save_path=config.KNOWLEDGE_GRAPH_IMAGE_PATH)
    print(f"Knowledge graph visualization saved to '{graph_path}'")
    
    end_time = time.time()
    print("\n--- Knowledge Asset Building Complete ---")
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")
    print(f"Processed {len(vector_store.vectors)} text items with embeddings.")
    print(f"Knowledge graph has {vector_store.graph.number_of_nodes()} nodes and {vector_store.graph.number_of_edges()} edges.")
    print("-----------------------------------------")

def analyze_dataset_stats(data_dir="dataset"):
    """Analyze and print statistics about the dataset"""
    bias_types = {}
    total_scenarios = 0
    total_dialogues = 0
    bias_level_counts = {0: 0, 10: 0, 30: 0, 50: 0, 70: 0, 100: 0}
    
    print(f"Analyzing dataset statistics in {data_dir}...")
    
    for filename in os.listdir(data_dir):
        if filename.startswith("bias_data_for_type_") and filename.endswith(".json"):
            bias_type = filename.split("bias_data_for_type_")[1].split(".json")[0]
            
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Count scenarios in this type
                scenarios_count = len(data)
                total_scenarios += scenarios_count
                
                dialogues_count = 0
                
                # Count dialogues and bias levels
                for item in data:
                    dialogues_count += len(item["parameters"]["conversations"])
                    
                    for conversation in item["parameters"]["conversations"]:
                        version = conversation["version"]
                        
                        # Count bias levels
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
                
                total_dialogues += dialogues_count
                
                # Store stats for this bias type
                bias_types[bias_type] = {
                    "scenarios": scenarios_count,
                    "dialogues": dialogues_count,
                    "avg_dialogues_per_scenario": dialogues_count / scenarios_count if scenarios_count > 0 else 0
                }
    
    # Print statistics
    print("\nDataset Statistics:")
    print(f"Total Bias Types: {len(bias_types)}")
    print(f"Total Scenarios: {total_scenarios}")
    print(f"Total Dialogues: {total_dialogues}")
    print(f"Average Dialogues per Scenario: {total_dialogues / total_scenarios:.2f}")
    
    print("\nBias Level Distribution:")
    total_bias_examples = sum(bias_level_counts.values())
    for level, count in bias_level_counts.items():
        percentage = (count / total_bias_examples) * 100 if total_bias_examples > 0 else 0
        print(f"  {level}% Bias: {count} examples ({percentage:.2f}%)")
    
    print("\nBias Types:")
    for bias_type, stats in bias_types.items():
        print(f"  {bias_type}:")
        print(f"    Scenarios: {stats['scenarios']}")
        print(f"    Dialogues: {stats['dialogues']}")
        print(f"    Avg Dialogues per Scenario: {stats['avg_dialogues_per_scenario']:.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build all knowledge assets (Vector Store, Graph Visualization) for the Bias Detection System."
    )
    # No force flag; prompt user if assets exist
    _ = parser.parse_args()
    build_knowledge_assets()