"""
Test script for Exercise 0: Simple Agentic Assistant

This script tests the Exercise 0 agent implementation without needing
to start the full WebSocket server.

Usage:
    python test_exercise_0.py
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from agents.hotel_simple_agent import answer_hotel_question


def test_exercise_0():
    """Test the Exercise 0 agent with sample queries."""
    
    # Check configuration
    try:
        from config.agent_config import get_agent_config
        config = get_agent_config()
        print(f"✅ Configuration loaded: provider={config.provider}, model={config.model}")
    except ValueError as e:
        print(f"❌ ERROR: Configuration error: {e}")
        print("Please set AI_AGENTIC_API_KEY environment variable or configure in config/agent_config.yaml")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to load configuration: {e}")
        return False
    
    print("🧪 Testing Exercise 0: Simple Agentic Assistant\n")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "List all hotels and their locations",
        "What is the address of the first hotel?",
        "What meal plans are available?",
        "Tell me about the rooms in these hotels"
    ]
    
    success_count = 0
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}/{len(test_queries)}: {query}")
        print("-" * 60)
        
        try:
            response = answer_hotel_question(query)
            print(f"✅ Response received ({len(response)} characters)")
            print(f"\n{response[:200]}...")  # Show first 200 chars
            success_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"\n📊 Results: {success_count}/{len(test_queries)} tests passed")
    
    if success_count == len(test_queries):
        print("✅ All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = test_exercise_0()
    sys.exit(0 if success else 1)

