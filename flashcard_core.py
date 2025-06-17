"""
Flashcard Generator - Core Module
Contains the main logic for generating flashcards from educational content
"""

import re
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM


class FlashcardGenerator:
    """Main class for generating flashcards using LLM"""
    
    def __init__(self, model_name: str = "google/flan-t5-base"):
        """Initialize the flashcard generator with specified model"""
        self.model_name = model_name
        self.generator = None
        self.load_model()
    
    def load_model(self):
        """Load the LLM model for text generation"""
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.generator = pipeline(
                "text2text-generation", 
                model=model, 
                tokenizer=tokenizer, 
                max_length=512
            )
            print(f"Model {self.model_name} loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.generator = None
    
    def split_into_chunks(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """Split text into smaller chunks for processing"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def generate_question_answer_pair(self, chunk: str) -> Dict[str, str]:
        """Generate a single question-answer pair from text chunk"""
        if not self.generator:
            return self.generate_fallback_pair(chunk)
        
        try:
            # Generate question
            question_prompt = f"Generate a clear, specific question about this text: {chunk}"
            question_result = self.generator(
                question_prompt, 
                max_length=100, 
                do_sample=True, 
                temperature=0.7
            )
            question = question_result[0]['generated_text'].strip()
            
            # Generate answer
            answer_prompt = f"Answer this question based on the text: {question}\n\nText: {chunk}"
            answer_result = self.generator(
                answer_prompt, 
                max_length=200, 
                do_sample=True, 
                temperature=0.7
            )
            answer = answer_result[0]['generated_text'].strip()
            
            # Clean up the generated text
            question = re.sub(r'^(Question:|Q:)\s*', '', question, flags=re.IGNORECASE)
            answer = re.sub(r'^(Answer:|A:)\s*', '', answer, flags=re.IGNORECASE)
            
            return {"question": question, "answer": answer}
            
        except Exception as e:
            print(f"Error generating Q&A pair: {e}")
            return self.generate_fallback_pair(chunk)
    
    def generate_fallback_pair(self, chunk: str) -> Dict[str, str]:
        """Generate basic question-answer pair without LLM"""
        words = chunk.split()
        if len(words) > 10:
            # Create fill-in-the-blank style question
            key_word = max(words, key=len)  # Find longest word as key term
            question = chunk.replace(key_word, "______", 1)
            answer = key_word
            
            return {
                "question": f"Fill in the blank: {question}",
                "answer": answer
            }
        
        return {
            "question": f"What is the main point of this text: {chunk[:100]}...?",
            "answer": chunk[:200] + "..." if len(chunk) > 200 else chunk
        }
    
    def assign_difficulty(self, question: str, answer: str) -> str:
        """Assign difficulty level based on question and answer complexity"""
        # Simple heuristic based on length and complexity
        total_length = len(question) + len(answer)
        complex_words = len([w for w in (question + " " + answer).split() if len(w) > 8])
        
        if total_length < 100 and complex_words < 2:
            return "Easy"
        elif total_length > 200 or complex_words > 5:
            return "Hard"
        else:
            return "Medium"
    
    def detect_topic(self, chunk: str, index: int) -> str:
        """Detect topic/subject from text chunk"""
        # Simple topic detection based on keywords
        science_keywords = ['experiment', 'hypothesis', 'theory', 'research', 'study', 'analysis']
        history_keywords = ['century', 'war', 'empire', 'revolution', 'ancient', 'medieval']
        math_keywords = ['equation', 'formula', 'calculate', 'theorem', 'proof', 'variable']
        
        chunk_lower = chunk.lower()
        
        if any(keyword in chunk_lower for keyword in science_keywords):
            return "Science"
        elif any(keyword in chunk_lower for keyword in history_keywords):
            return "History"
        elif any(keyword in chunk_lower for keyword in math_keywords):
            return "Mathematics"
        else:
            return f"Section {index + 1}"
    
    def generate_flashcards(self, text: str, num_cards: int = 15) -> List[Dict[str, Any]]:
        """Generate flashcards from input text"""
        if not text or len(text.strip()) < 50:
            return []
        
        flashcards = []
        chunks = self.split_into_chunks(text, 400)
        
        for i, chunk in enumerate(chunks[:num_cards]):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            # Generate question-answer pair
            qa_pair = self.generate_question_answer_pair(chunk)
            
            if qa_pair["question"] and qa_pair["answer"] and \
               len(qa_pair["question"]) > 10 and len(qa_pair["answer"]) > 10:
                
                flashcard = {
                    "question": qa_pair["question"],
                    "answer": qa_pair["answer"],
                    "difficulty": self.assign_difficulty(qa_pair["question"], qa_pair["answer"]),
                    "topic": self.detect_topic(chunk, i)
                }
                
                flashcards.append(flashcard)
        
        return flashcards


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""


def process_educational_content(content: str, file_path: str = None) -> List[Dict[str, Any]]:
    """Main function to process educational content and generate flashcards"""
    generator = FlashcardGenerator()
    
    # Extract text from file if provided
    if file_path:
        if file_path.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
    
    # Generate flashcards
    flashcards = generator.generate_flashcards(content)
    
    return flashcards

