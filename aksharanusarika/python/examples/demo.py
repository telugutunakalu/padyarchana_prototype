# -*- coding: utf-8 -*-
"""
Quick Demo of the New JSON Output Feature
"""
from aksharanusarika import generate_comprehensive_json
import json

print("=" * 60)
print("AKSHARANUSARIKA - COMPREHENSIVE JSON OUTPUT DEMO")
print("=" * 60)

# Demo: Analyze a Telugu word and save to JSON
word = "తెలుగు"
print(f"\nAnalyzing: '{word}'")
print("-" * 60)

# Generate and save JSON
generate_comprehensive_json(word, "demo_output.json")
print("✓ Analysis saved to demo_output.json")

# Read and display key metrics
with open("demo_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("\nKey Metrics:")
print(f"  Total Aksharas: {data['linguistic']['statistics']['totalAksharas']}")
print(f"  Vowels: {data['linguistic']['statistics']['vowelCount']}")
print(f"  Consonants: {data['linguistic']['statistics']['consonantCount']}")
print(f"  Gana Pattern: {' '.join(data['prosody']['ganaSequence'])}")
print(f"  Gana Combinations: {data['prosody']['ganaCombinations']['count']}")
print(f"  Processing Time: {data['metadata']['processingTimeMs']}ms")

print("\nSummary:")
print(f"  {data['summary']['linguisticProfile']}")
print(f"  {data['summary']['prosodicProfile']}")

print("\n" + "=" * 60)
print("Demo complete! Check 'demo_output.json' for full analysis.")
print("=" * 60)
