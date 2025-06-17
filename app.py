from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import re
import json
import csv
import io
import os
from werkzeug.utils import secure_filename
import PyPDF2

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the text generation pipeline
try:
    # Use a smaller, more efficient model for Q&A generation
    model_name = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=512)
    print(f"Model {model_name} loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    # Fallback to a simpler approach
    generator = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def split_into_chunks(text, max_chunk_size=500):
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

def generate_flashcards_from_text(text, num_cards=15):
    """Generate flashcards from input text using LLM"""
    if not generator:
        # Fallback method without LLM
        return generate_fallback_flashcards(text)
    
    flashcards = []
    chunks = split_into_chunks(text, 400)
    
    for i, chunk in enumerate(chunks[:num_cards]):
        if len(chunk.strip()) < 50:  # Skip very short chunks
            continue
            
        try:
            # Generate question
            question_prompt = f"Generate a clear, specific question about this text: {chunk}"
            question_result = generator(question_prompt, max_length=100, do_sample=True, temperature=0.7)
            question = question_result[0]['generated_text'].strip()
            
            # Generate answer
            answer_prompt = f"Answer this question based on the text: {question}\n\nText: {chunk}"
            answer_result = generator(answer_prompt, max_length=200, do_sample=True, temperature=0.7)
            answer = answer_result[0]['generated_text'].strip()
            
            # Clean up the generated text
            question = re.sub(r'^(Question:|Q:)\s*', '', question, flags=re.IGNORECASE)
            answer = re.sub(r'^(Answer:|A:)\s*', '', answer, flags=re.IGNORECASE)
            
            if question and answer and len(question) > 10 and len(answer) > 10:
                flashcards.append({
                    "question": question,
                    "answer": answer,
                    "difficulty": "Medium",  # Default difficulty
                    "topic": f"Section {i+1}"
                })
                
        except Exception as e:
            print(f"Error generating flashcard {i}: {e}")
            continue
    
    # If we don't have enough cards, add some fallback ones
    if len(flashcards) < 5:
        fallback_cards = generate_fallback_flashcards(text)
        flashcards.extend(fallback_cards[:10-len(flashcards)])
    
    return flashcards

def generate_fallback_flashcards(text):
    """Generate basic flashcards without LLM as fallback"""
    sentences = re.split(r'[.!?]+', text)
    important_sentences = [s.strip() for s in sentences if len(s.strip()) > 50][:10]
    
    flashcards = []
    for i, sentence in enumerate(important_sentences):
        # Create simple question-answer pairs
        words = sentence.split()
        if len(words) > 10:
            # Create fill-in-the-blank style questions
            key_word = max(words, key=len)  # Find longest word as key term
            question = sentence.replace(key_word, "______", 1)
            answer = key_word
            
            flashcards.append({
                "question": f"Fill in the blank: {question}",
                "answer": answer,
                "difficulty": "Easy",
                "topic": f"Section {i+1}"
            })
    
    return flashcards

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_flashcards', methods=['POST'])
def generate_flashcards():
    try:
        content = ""
        
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                if filename.lower().endswith('.pdf'):
                    content = extract_text_from_pdf(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                # Clean up uploaded file
                os.remove(file_path)
        
        # Check for text input
        if not content and 'content' in request.form:
            content = request.form['content']
        
        if not content:
            return jsonify({"error": "No content provided"}), 400
        
        # Generate flashcards
        flashcards = generate_flashcards_from_text(content)
        
        if not flashcards:
            return jsonify({"error": "Could not generate flashcards from the provided content"}), 400
        
        return jsonify(flashcards)
        
    except Exception as e:
        print(f"Error in generate_flashcards: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/export/<format>')
def export_flashcards(format):
    """Export flashcards in different formats"""
    flashcards_data = request.args.get('data')
    if not flashcards_data:
        return jsonify({"error": "No flashcard data provided"}), 400
    
    try:
        flashcards = json.loads(flashcards_data)
        
        if format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Question', 'Answer', 'Difficulty', 'Topic'])
            
            for card in flashcards:
                writer.writerow([
                    card.get('question', ''),
                    card.get('answer', ''),
                    card.get('difficulty', 'Medium'),
                    card.get('topic', '')
                ])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name='flashcards.csv'
            )
        
        elif format == 'json':
            return send_file(
                io.BytesIO(json.dumps(flashcards, indent=2).encode()),
                mimetype='application/json',
                as_attachment=True,
                download_name='flashcards.json'
            )
        
        else:
            return jsonify({"error": "Unsupported export format"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

