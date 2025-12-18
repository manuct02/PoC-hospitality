"""
Test para las Tools de la Phase 4
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_rag_agent import (
    search_hotels_by_city,
    count_rooms
)

def test_tools():
    """Prueba las herramientas del agente"""
    
    print("\n" + "="*70)
    print("🧪 TESTING PHASE 4: Agent Tools")
    print("="*70 + "\n")
    
    # Test 1: Buscar hoteles por ciudad
    print("📍 Test 1: Search hotels by city (Paris)")
    print("-" * 70)
    try:
        result = search_hotels_by_city("Paris")
        print(result)
        print("\n✅ Test 1 passed\n")
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}\n")
    
    # Test 2: Buscar en ciudad que no existe
    print("\n📍 Test 2: Search hotels in non-existent city (Berlin)")
    print("-" * 70)
    try:
        result = search_hotels_by_city("Berlin")
        print(result)
        print("\n✅ Test 2 passed\n")
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}\n")
    
    # Test 3: Contar todas las habitaciones
    print("\n🔢 Test 3: Count all rooms")
    print("-" * 70)
    try:
        result = count_rooms()
        print(result)
        print("\n✅ Test 3 passed\n")
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}\n")
    
    # Test 4: Contar habitaciones en París
    print("\n🔢 Test 4: Count rooms in Paris")
    print("-" * 70)
    try:
        result = count_rooms(city="Paris")
        print(result)
        print("\n✅ Test 4 passed\n")
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}\n")
    
    # Test 5: Contar habitaciones dobles
    print("\n🔢 Test 5: Count Double rooms")
    print("-" * 70)
    try:
        result = count_rooms(room_type="Double")
        print(result)
        print("\n✅ Test 5 passed\n")
    except Exception as e:
        print(f"\n❌ Test 5 failed: {e}\n")
    
    # Test 6: Contar habitaciones dobles en Nice
    print("\n🔢 Test 6: Count Double rooms in Nice")
    print("-" * 70)
    try:
        result = count_rooms(city="Nice", room_type="Double")
        print(result)
        print("\n✅ Test 6 passed\n")
    except Exception as e:
        print(f"\n❌ Test 6 failed: {e}\n")
    
    print("="*70)
    print("🎉 TOOLS TESTING COMPLETED")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_tools()
