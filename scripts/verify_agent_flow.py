"""Verification script to test the end-to-end multi-agent flow."""
import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent.pain_point_agent import run_agent

def main():
    query = "Where can I find discussions about common issues with Shopify billing?"
    print(f"Running agent with query: '{query}'")
    
    try:
        result = run_agent(query)
        print("\n--- Result Metadata ---")
        print(json.dumps(result.get("metadata", {}), indent=2))
        
        print("\n--- Pain Points Found ---")
        pain_points = result.get("pain_points", [])
        print(f"Count: {len(pain_points)}")
        if pain_points:
            print(json.dumps(pain_points[0], indent=2)) # Print first one as sample
            
    except Exception as e:
        print(f"\nERROR: {e}")
        raise

if __name__ == "__main__":
    main()
