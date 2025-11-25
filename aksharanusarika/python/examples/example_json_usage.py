# -*- coding: utf-8 -*-
"""
Example Usage of generate_comprehensive_json() Function
========================================================

This script demonstrates how to use the new comprehensive JSON output feature
in aksharanusarika.py to analyze Telugu text.
"""

from aksharanusarika import generate_comprehensive_json
import json

# Example 1: Analyze a single Telugu letter
print("Example 1: Single Letter Analysis")
print("-" * 50)
result = generate_comprehensive_json("తే")
print(f"Input: {result['input']['rawText']}")
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Gana Pattern: {' '.join(result['prosody']['ganaSequence'])}")
print()

# Example 2: Analyze a Telugu word
print("Example 2: Word Analysis")
print("-" * 50)
result = generate_comprehensive_json("తెలుగు")
print(f"Input: {result['input']['rawText']}")
print(f"Aksharas: {', '.join(result['linguistic']['aksharaluList'])}")
print(f"Vowels: {result['linguistic']['statistics']['vowelCount']}")
print(f"Consonants: {result['linguistic']['statistics']['consonantCount']}")
print(f"Gana Sequence: {' '.join(result['prosody']['ganaSequence'])}")
print(f"Summary: {result['summary']['linguisticProfile']}")
print()

# Example 3: Analyze a Telugu sentence
print("Example 3: Sentence Analysis")
print("-" * 50)
sentence = "తెలుగు వికీపీడియా ఆవిర్భావానికి"
result = generate_comprehensive_json(sentence)
print(f"Input: {result['input']['rawText']}")
print(f"Word Count: {result['input']['wordCount']}")
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Unique Aksharas: {result['linguistic']['statistics']['uniqueAksharas']}")
print(f"Guru/Laghu Ratio: {result['prosody']['statistics']['guruToLaghuRatio']}")
print(f"Gana Combinations: {result['prosody']['ganaCombinations']['count']}")
print()

# Example 4: Save analysis to JSON file
print("Example 4: Save to JSON File")
print("-" * 50)
word = "సత్యము"
output_file = "my_telugu_analysis.json"
message = generate_comprehensive_json(word, output_file)
print(message)
print(f"You can now open '{output_file}' to see the complete analysis")
print()

# Example 5: Analyze a paragraph
print("Example 5: Paragraph Analysis")
print("-" * 50)
paragraph = """తెలుగు భాష దక్షిణ భారతదేశంలో తెలుగు ప్రజలు మాట్లాడే భాష.
ఆంధ్రప్రదేశ్, తెలంగాణ రాష్ట్రాల అధికార భాష."""

result = generate_comprehensive_json(paragraph)
print(f"Character Count: {result['input']['characterCount']}")
print(f"Word Count: {result['input']['wordCount']}")
print(f"Sentence Count: {result['input']['sentenceCount']}")
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Complexity Score: {result['linguistic']['statistics']['complexityScore']}%")
print(f"Dominant Categories: {', '.join(result['summary']['dominantCategories'][:3])}")
print(f"Prosodic Profile: {result['summary']['prosodicProfile']}")
print()

# Example 6: Access specific linguistic features
print("Example 6: Detailed Linguistic Analysis")
print("-" * 50)
word = "సందడి"
result = generate_comprehensive_json(word)

print(f"Input: {result['input']['rawText']}")
print(f"\nVargam Distribution:")
for vargam, count in result['linguistic']['vargamDistribution'].items():
    if count > 0:
        print(f"  {vargam}: {count}")

print(f"\nArticulation Distribution:")
for place, count in result['linguistic']['articulationDistribution'].items():
    if count > 0:
        print(f"  {place}: {count}")

print(f"\nGana Details:")
for marker in result['prosody']['ganaMarkers']:
    print(f"  {marker['aksharam']} → {marker['marker']}")

print()

# Example 7: Pretty print full JSON to console
print("Example 7: Full JSON Output")
print("-" * 50)
result = generate_comprehensive_json("అమ్మ")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "="*50)
print("All examples completed successfully!")
print("="*50)
