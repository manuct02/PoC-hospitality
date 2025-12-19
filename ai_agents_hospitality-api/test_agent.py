"""
Test para el Agente completo con Tools (Phase 4)
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import invoke_agent_with_tools

async def test_agent():
    """Prueba el agente completo con diferentes queries"""
    
    print("\n" + "="*70)
    print("🤖 TESTING PHASE 4: Complete Agent with Tools")
    print("="*70 + "\n")
    
    # Queries de prueba - solo preguntas naturales, sin pistas para el agente
    test_queries = ["list all hotels in France, just the names"]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"📝 Test {i}")
        print(f"Query: {query}")
        print('='*70)
        
        try:
            response = await invoke_agent_with_tools(query)
            print(f"\n✅ Response:\n{response}\n")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("🎉 AGENT TESTING COMPLETED")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_agent())
