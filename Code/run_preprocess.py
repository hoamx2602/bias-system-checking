"""Entry point: builds the vector store and knowledge graph visualization."""
from src.data.preprocess import build_knowledge_assets

if __name__ == '__main__':
    build_knowledge_assets()
