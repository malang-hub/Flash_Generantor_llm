#!/usr/bin/env python3
"""
Test script for the Flashcard Generator
Demonstrates the core functionality with sample content
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flashcard_core import FlashcardGenerator
from sample_content import BIOLOGY_SAMPLE, HISTORY_SAMPLE, COMPUTER_SCIENCE_SAMPLE


def test_flashcard_generation():
    """Test flashcard generation with sample content"""
    print("🧪 Testing Flashcard Generator")
    print("=" * 50)
    
    generator = FlashcardGenerator()
    
    # Test with biology content
    print("\n📚 Testing with Biology Content:")
    print("-" * 30)
    biology_cards = generator.generate_flashcards(BIOLOGY_SAMPLE, num_cards=5)
    
    for i, card in enumerate(biology_cards, 1):
        print(f"\nCard {i}:")
        print(f"Topic: {card['topic']}")
        print(f"Difficulty: {card['difficulty']}")
        print(f"Q: {card['question']}")
        print(f"A: {card['answer'][:100]}...")
    
    # Test with history content
    print("\n\n🏛️ Testing with History Content:")
    print("-" * 30)
    history_cards = generator.generate_flashcards(HISTORY_SAMPLE, num_cards=3)
    
    for i, card in enumerate(history_cards, 1):
        print(f"\nCard {i}:")
        print(f"Topic: {card['topic']}")
        print(f"Difficulty: {card['difficulty']}")
        print(f"Q: {card['question']}")
        print(f"A: {card['answer'][:100]}...")
    
    # Test with computer science content
    print("\n\n💻 Testing with Computer Science Content:")
    print("-" * 30)
    cs_cards = generator.generate_flashcards(COMPUTER_SCIENCE_SAMPLE, num_cards=4)
    
    for i, card in enumerate(cs_cards, 1):
        print(f"\nCard {i}:")
        print(f"Topic: {card['topic']}")
        print(f"Difficulty: {card['difficulty']}")
        print(f"Q: {card['question']}")
        print(f"A: {card['answer'][:100]}...")
    
    print(f"\n✅ Test completed successfully!")
    print(f"Generated {len(biology_cards) + len(history_cards) + len(cs_cards)} total flashcards")


if __name__ == "__main__":
    test_flashcard_generation()

