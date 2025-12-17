"""
Script de prueba para la Phase 2: Vector Store Creation
"""
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import (
    load_hotel_documents,
    split_documents,
    get_or_create_vectorstore
)
from util.logger_config import logger

def test_phase2():
    """Prueba las funciones de la Phase 2"""
    
    print("\n" + "="*60)
    print("🧪 TESTING PHASE 2: Vector Store Creation")
    print("="*60 + "\n")
    
    # Test 1: Cargar documentos
    print("📄 Test 1: Loading documents...")
    try:
        documents = load_hotel_documents()
        print(f"✅ Loaded {len(documents)} documents")
        if documents:
            print(f"   First doc preview: {documents[0].page_content[:100]}...")
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return
    
    # Test 2: Chunkear documentos
    print("\n✂️  Test 2: Splitting documents into chunks...")
    try:
        chunks = split_documents(documents)
        print(f"✅ Created {len(chunks)} chunks")
        if chunks:
            print(f"   First chunk preview: {chunks[0].page_content[:100]}...")
    except Exception as e:
        print(f"❌ Error splitting documents: {e}")
        return
    
    # Test 3: Crear vectorstore
    print("\n🗄️  Test 3: Creating vector store (this may take a while)...")
    try:
        vectorstore = get_or_create_vectorstore(force_rebuild=True)
        print(f"✅ Vector store created successfully!")
        print(f"   Persisted to: vector_store/")
        
        # Test 4: Probar búsqueda simple
        print("\n🔍 Test 4: Testing similarity search...")
        results = vectorstore.similarity_search("hotels in Paris", k=3)
        print(f"✅ Found {len(results)} similar documents")
        for i, doc in enumerate(results, 1):
            print(f"   Result {i}: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"❌ Error creating vector store: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("🎉 PHASE 2 TEST COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_phase2()
