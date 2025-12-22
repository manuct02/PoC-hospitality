"""
Test de Performance - Exercise 1
Verifica que las queries respondan en < 10 segundos
"""
import sys
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import invoke_agent_with_tools

async def test_performance():
    """Prueba el tiempo de respuesta del agente"""
    
    print("\n" + "="*70)
    print("⏱️  PERFORMANCE TEST - Exercise 1 RAG Agent")
    print("="*70 + "\n")
    
    # Queries de prueba (variedad de casos)
    test_queries = [
        "List hotels in Paris",
        "How many rooms are there in Nice?",
        "What are the prices for double rooms in Cannes?",
        "What is the full address of Obsidian Tower?",
        "List all hotels in France",
        "Tell me about meal charges for Half Board",
        "Compare room prices between peak and off season in Nice"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_queries)}: {query}")
        print('='*70)
        
        try:
            # Medir tiempo de inicio
            start_time = time.time()
            
            # Ejecutar query
            response = await invoke_agent_with_tools(query)
            
            # Medir tiempo de fin
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Guardar resultado
            results.append({
                'query': query,
                'time': elapsed,
                'success': True
            })
            
            # Mostrar resultado
            status = "✅ PASS" if elapsed < 10 else "❌ FAIL"
            print(f"\n{status} - Time: {elapsed:.2f}s")
            print(f"Response preview: {response[:100]}...")
            
        except Exception as e:
            # Error
            results.append({
                'query': query,
                'time': 0,
                'success': False,
                'error': str(e)
            })
            print(f"\n❌ ERROR: {e}")
    
    # ========== REPORTE FINAL ==========
    print("\n" + "="*70)
    print("📊 PERFORMANCE REPORT")
    print("="*70 + "\n")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        times = [r['time'] for r in successful]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"✅ Successful queries: {len(successful)}/{len(results)}")
        print(f"⏱️  Average time: {avg_time:.2f}s")
        print(f"⚡ Fastest: {min_time:.2f}s")
        print(f"🐌 Slowest: {max_time:.2f}s")
        
        # Verificar requirement (< 10s)
        over_10s = [r for r in successful if r['time'] >= 10]
        
        if over_10s:
            print(f"\n❌ FAILED: {len(over_10s)} queries took >= 10s:")
            for r in over_10s:
                print(f"   - {r['query'][:50]}... ({r['time']:.2f}s)")
        else:
            print(f"\n✅ PASSED: All queries under 10 seconds!")
    
    if failed:
        print(f"\n❌ Failed queries: {len(failed)}")
        for r in failed:
            print(f"   - {r['query'][:50]}...")
    
    print("\n" + "="*70)
    print("Detailed Results:")
    print("="*70 + "\n")
    
    for i, r in enumerate(results, 1):
        status = "✅" if r['success'] and r['time'] < 10 else "❌"
        time_str = f"{r['time']:.2f}s" if r['success'] else "ERROR"
        print(f"{status} [{time_str:>8}] {r['query']}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_performance())
