# -*- coding: utf-8 -*-
"""
Test script for the new JSON output feature
"""
import sys
import json
from aksharanusarika import generate_comprehensive_json

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print("="*60)
print("TESTING COMPREHENSIVE JSON OUTPUT FEATURE")
print("="*60)

# Test 1: Single Letter
print("\n[Test 1: Single Letter 'తే']")
result1 = generate_comprehensive_json("తే")
print(f"✓ Total Aksharas: {result1['linguistic']['statistics']['totalAksharas']}")
print(f"✓ Gana: {result1['prosody']['ganaSequence']}")
print(f"✓ Processing Time: {result1['metadata']['processingTimeMs']}ms")

# Test 2: Word
print("\n[Test 2: Word 'తెలుగు']")
result2 = generate_comprehensive_json("తెలుగు")
print(f"✓ Total Aksharas: {result2['linguistic']['statistics']['totalAksharas']}")
print(f"✓ Vowels: {result2['linguistic']['statistics']['vowelCount']}")
print(f"✓ Consonants: {result2['linguistic']['statistics']['consonantCount']}")
print(f"✓ Gana Sequence: {' '.join(result2['prosody']['ganaSequence'])}")

# Test 3: Sentence
print("\n[Test 3: Sentence 'తెలుగు వికీపీడియా']")
result3 = generate_comprehensive_json("తెలుగు వికీపీడియా")
print(f"✓ Word Count: {result3['input']['wordCount']}")
print(f"✓ Total Aksharas: {result3['linguistic']['statistics']['totalAksharas']}")
print(f"✓ Unique Aksharas: {result3['linguistic']['statistics']['uniqueAksharas']}")
print(f"✓ Guru Count: {result3['prosody']['statistics']['guruCount']}")
print(f"✓ Laghu Count: {result3['prosody']['statistics']['laghuCount']}")

# Test 4: Save to file
print("\n[Test 4: Saving to JSON file]")
output_msg = generate_comprehensive_json("సత్యము", "telugu_analysis_output.json")
print(f"✓ {output_msg}")

# Verify file was created and read it back
print("\n[Test 5: Verify JSON file contents]")
with open("telugu_analysis_output.json", 'r', encoding='utf-8') as f:
    file_data = json.load(f)
    print(f"✓ File loaded successfully")
    print(f"✓ Input text: {file_data['input']['rawText']}")
    print(f"✓ Schema version: {file_data['metadata']['schemaVersion']}")
    print(f"✓ Analyzer version: {file_data['metadata']['analyzerVersion']}")

# Test 6: Complex paragraph
print("\n[Test 6: Paragraph analysis]")
paragraph = """తెలుగు భాష దక్షిణ భారతదేశంలో తెలుగు ప్రజలు మాట్లాడే భాష.
ఆంధ్రప్రదేశ్, తెలంగాణ రాష్ట్రాల అధికార భాష."""

result6 = generate_comprehensive_json(paragraph)
print(f"✓ Character Count: {result6['input']['characterCount']}")
print(f"✓ Word Count: {result6['input']['wordCount']}")
print(f"✓ Sentence Count: {result6['input']['sentenceCount']}")
print(f"✓ Total Aksharas: {result6['linguistic']['statistics']['totalAksharas']}")
print(f"✓ Complexity Score: {result6['linguistic']['statistics']['complexityScore']}%")
print(f"✓ Dominant Categories: {', '.join(result6['summary']['dominantCategories'])}")

# Save paragraph analysis to file
generate_comprehensive_json(paragraph, "paragraph_analysis.json")
print("✓ Paragraph analysis saved to paragraph_analysis.json")

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nUsage Examples:")
print("  # Return as dictionary:")
print("  result = generate_comprehensive_json('తెలుగు పదం')")
print("\n  # Save to file:")
print("  generate_comprehensive_json('తెలుగు పదం', 'output.json')")
print("\nGenerated files:")
print("  - telugu_analysis_output.json")
print("  - paragraph_analysis.json")
