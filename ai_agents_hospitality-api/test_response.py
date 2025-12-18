"""
Test para Phase 3: RAG Chain Implementation
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import handle_hotel_query_rag

async def test_phase3():
    print("\n🧪 Testing Phase 3: RAG Chain\n")
    
    query = "Dime el precio de la habitación 3 del segundo hotel en la lista."
    print(f"Query: {query}\n")
    
    try:
        response = await handle_hotel_query_rag(query)
        print(f"✅ Response:\n{response}\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phase3())