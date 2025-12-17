"""Debug: Ver qué chunks recupera para Berlin"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import get_or_create_vectorstore

vectorstore = get_or_create_vectorstore()
results = vectorstore.similarity_search("hotels in Berlin", k=5)

print("\n🔍 Chunks recuperados para 'hotels in Berlin':\n")
for i, doc in enumerate(results, 1):
    print(f"--- Chunk {i} ---")
    print(doc.page_content[:300])
    print()