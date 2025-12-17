"""
Verification script to check if Exercise 0 agent is properly integrated.

This script checks:
1. If the agent module can be imported
2. If hotel data files exist
3. If environment variables are set
4. If the agent can be initialized
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

print("🔍 Verifying Exercise 0 Agent Integration\n")
print("=" * 60)

# Check 1: Configuration system
print("\n1️⃣  Checking configuration system...")
try:
    from config.agent_config import get_agent_config
    config = get_agent_config()
    print(f"   ✅ Configuration loaded successfully")
    print(f"   - Provider: {config.provider}")
    print(f"   - Model: {config.model}")
    print(f"   - Temperature: {config.temperature}")
    print(f"   - API Key: {'✅ Set' if config.api_key else '❌ Not set'} ({len(config.api_key) if config.api_key else 0} characters)")
except Exception as e:
    print(f"   ❌ Error loading configuration: {e}")
    sys.exit(1)

# Check 2: Hotel data files
print("\n2️⃣  Checking hotel data files...")
from util.configuration import PROJECT_ROOT

HOTELS_DATA_PATH = PROJECT_ROOT.parent / "bookings-db" / "output_files" / "hotels"
HOTELS_JSON_FILE = HOTELS_DATA_PATH / "hotels.json"
HOTEL_DETAILS_FILE = HOTELS_DATA_PATH / "hotel_details.md"

if HOTELS_JSON_FILE.exists():
    print(f"   ✅ hotels.json exists: {HOTELS_JSON_FILE}")
else:
    print(f"   ❌ hotels.json NOT found: {HOTELS_JSON_FILE}")

if HOTEL_DETAILS_FILE.exists():
    print(f"   ✅ hotel_details.md exists: {HOTEL_DETAILS_FILE}")
else:
    print(f"   ❌ hotel_details.md NOT found: {HOTEL_DETAILS_FILE}")

# Check 3: Agent module import
print("\n3️⃣  Checking agent module import...")
try:
    from agents.hotel_simple_agent import handle_hotel_query_simple, load_hotel_data
    print("   ✅ Agent module imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import agent module: {e}")
    print("   💡 Try: pip install langchain langchain-openai")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error importing agent module: {e}")
    sys.exit(1)

# Check 4: Load hotel data
print("\n4️⃣  Checking hotel data loading...")
try:
    hotels_data, hotel_details = load_hotel_data()
    num_hotels = len(hotels_data.get('hotels', []))
    print(f"   ✅ Hotel data loaded successfully ({num_hotels} hotels)")
except FileNotFoundError as e:
    print(f"   ❌ Hotel data files not found: {e}")
    print("   💡 Generate data with: cd bookings-db && python src/gen_synthetic_hotels.py --num_hotels 3")
except Exception as e:
    print(f"   ❌ Error loading hotel data: {e}")

# Check 5: Agent initialization (test with a simple query)
print("\n5️⃣  Testing agent with a simple query...")
try:
    if not config.api_key:
        print("   ⚠️  Cannot test agent (missing API key)")
    else:
        # Try a simple synchronous call to test the agent
        from agents.hotel_simple_agent import answer_hotel_question
        test_response = answer_hotel_question("List all hotels")
        if test_response and len(test_response) > 0:
            print(f"   ✅ Agent responded successfully ({len(test_response)} characters)")
        else:
            print("   ⚠️  Agent responded but with empty content")
except ValueError as e:
    print(f"   ❌ Agent test failed: {e}")
except Exception as e:
    print(f"   ⚠️  Agent test error: {e}")
    print("   (This might be OK if API credentials are invalid or network issues)")

# Summary
print("\n" + "=" * 60)
print("\n📊 Integration Summary:")
print("\nTo use Exercise 0 agent, ensure:")
print("  ✅ Configuration is properly set (check config/agent_config.yaml or environment variables)")
print("  ✅ Hotel data files exist (hotels.json, hotel_details.md)")
print("  ✅ LangChain dependencies are installed")
print("\nIf all checks pass, the agent should work in the WebSocket endpoint.")
print("\n" + "=" * 60)

