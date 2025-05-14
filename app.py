from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import random,re
import fitz  #PyMuPDF for PDF processing
import spacy
from transformers import pipeline
from PIL import Image

app = Flask(__name__)

FILES_FOLDER = 'files/'  # Folder where files are stored

#_____________________________________________#

responses = {
    "hello": ["Hi there!", "Hello!", "Hey! How can I help you?"],
    "how are you": ["I'm good, thank you!", "I'm doing great! How about you?", "I'm just a bot, but I'm doing fine!"],
    "bye": ["Goodbye!", "See you later!", "Bye, have a nice day!"],
    "oiii": ["oiii","meawwww"],
    "ugh":["seems that you are mad","im sorry to have made this mistake"],
    "love you":["i love you too","i love you more","i too love you","meaew"],
    "default": ["Sorry, I don't understand that.", "Can you rephrase?", "I'm not sure how to respond to that."],
}

summarizer = pipeline("summarization", model="t5-small")
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

nlp = spacy.load("en_core_web_sm")
quiz_sessions = {}  # Track active quiz sessions

SUMMARY_LOG= "summary.json"

#_____________________________________________#
stack=[]


def get_previous_summary(input_text):
    """Check if a similar input was summarized before."""
    try:
        if os.path.exists(SUMMARY_LOG):
            with open(SUMMARY_LOG, "r") as f:
                data = json.load(f)
            for key in data:
                if key in input_text:  # Partial match
                    return data[key]
        return None
    except Exception as e:
        print("Error retrieving summary:", e)
        return None

def summarize_text(text):
    """Summarizes a given text using transformers."""
    if len(text) < 50:
        return "Text is too short for summarization."
    
    # Check if a similar summary already exists
    previous_summary = get_previous_summary(text)
    if previous_summary:
        return previous_summary  # Reuse stored summary

    # Chunk the text if it's too long
    chunks = chunk_text(text)

    # Summarize each chunk and combine summaries
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=200, min_length=100, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    
    # Combine the individual summaries
    final_summary = " ".join(summaries)

    return final_summary

def generate_questions(text):
    """Generate multiple-choice questions from a given text using NLP."""
    doc = nlp(text)  # Process text with spaCy
    sentences = [sent.text for sent in doc.sents]  # Tokenize sentences
    words = [token.text for token in doc if token.is_alpha]  # Extract words
    questions = []

    random.shuffle(sentences)

    for sentence in sentences:
        doc_sentence = nlp(sentence)
        words_in_sentence = sentence.split()

        # Find key words (nouns, verbs, named entities) for blanking
        blank_candidates = [token.text for token in doc_sentence if token.pos_ in {"NOUN", "VERB"} or token.ent_type_]
        
        if len(words_in_sentence) > 5 and blank_candidates:
            correct_answer = random.choice(blank_candidates)  # Select a key word
            
            # Generate incorrect answers (words of the same type)
            pos_tag = next((token.pos_ for token in doc_sentence if token.text == correct_answer), None)
            incorrect_answers = [token.text for token in doc if token.pos_ == pos_tag and token.text != correct_answer]
            incorrect_answers = random.sample(incorrect_answers, min(3, len(incorrect_answers))) if incorrect_answers else random.sample(words, 3)

            # Shuffle options
            options = [correct_answer] + incorrect_answers
            random.shuffle(options)

            # Format question
            question_text = sentence.replace(correct_answer, "_____")

            # Debugging output
            print(f"Generated Question: {question_text}")
            print(f"Options: {options}")
            print(f"Correct Answer: {correct_answer}")

            questions.append((question_text, correct_answer, options))
    
    return questions[:5]  # Limit to 5 questions

def start_quiz(user_id, text):
    questions = generate_questions(text)
    if not questions:
        return "No questions could be generated."

    quiz_sessions[user_id] = {
        "questions": questions,
        "current_question": 0,
        "score": 0
    }
    print(f"Quiz session for {user_id}: {quiz_sessions[user_id]}")  # Debug
    return ask_question(user_id)

def ask_question(user_id):
    session = quiz_sessions.get(user_id)
    if not session:
        return "No active quiz session found."

    question_index = session["current_question"]
    if question_index >= len(session["questions"]):
        return f"Quiz complete! Your score: {session['score']}/{len(session['questions'])}"

    question, correct_answer, options = session["questions"][question_index]
    return f"Question {question_index + 1}: {question}\nOptions: {', '.join(options)}"

def check_answer(user_id, user_answer):
    session = quiz_sessions.get(user_id)
    if not session:
        return "No active quiz session found."

    question_index = session["current_question"]
    question, correct_answer, options = session["questions"][question_index]

    if user_answer.lower() == correct_answer.lower():
        session["score"] += 1
        response = "Correct!"
    else:
        response = f"Incorrect. The correct answer was: {correct_answer}"

    session["current_question"] += 1
    return response + "\n" + ask_question(user_id)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file with fallback to OCR if needed."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"

        # If no text is extracted, try OCR
        if not text.strip():
            text = pytesseract.image_to_string(pdf_path)
            
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def get_important_points(pdf_path, max_chunk_size=2000):
    """Extracts and lists the important points from a PDF file."""
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    
    # If no text was extracted, return an error
    if not text.strip():
        return "No text found in the file or unable to extract text."

    # Chunk the text to manageable size for the summarizer (if needed)
    chunks = chunk_text(text, max_chunk_size)
    
    # Generate a summary for each chunk
    important_points = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=200, min_length=50, do_sample=False)
        important_points.append(summary[0]['summary_text'])
    
    return important_points

def list_files(search=None):
    """List all files in the files folder, optionally filtering by search text."""
    files = os.listdir(FILES_FOLDER)
    if search:
        files = [f for f in files if search.lower() in f.lower()]
    return files

def chunk_text(text, max_chunk_size=2000):
    """Chunk long text to manageable size for summarization."""
    chunks = []
    while len(text) > max_chunk_size:
        # Break text into chunks and process them
        chunk = text[:max_chunk_size]
        text = text[max_chunk_size:]
        chunks.append(chunk)
    chunks.append(text)
    return chunks

def show_files():
    """Return a list of files available in the files folder."""
    files = list_files()
    if files:
        return "Here are the available files:\n" + "\n".join(files), None
    return "No files found in the folder.", None

def get_response(user_input):
    """Generate a response based on user input."""
    user_input = user_input.lower()
    
    if "summarize this" in user_input:
        # Extract the custom text that the user wants to summarize
        custom_text = user_input.split("summarize this", 1)[1].strip()
        if custom_text:
            summary = summarize_text(custom_text)
            return f"Here is the summary:\n{summary}", None
        return "Please provide the content you'd like to summarize.", None
    
    if "files" in user_input or "show me files" in user_input:
        files = list_files()
        if files:
            # links for files
            links = [
                f'<a href="/files/{file}" target="_blank">{file}</a>' for file in files
            ]
            return "Here are the available files: <br>" + "<br>".join(links), None
        return "No files found in the folder.", None

    if user_input.startswith("open "):
        if "last opened file" in user_input:
            if stack:
                file_name=stack[-1]

        file_name = user_input.split("open ", 1)[1].strip()
        if os.path.exists(os.path.join(FILES_FOLDER, file_name)):
            stack.append(file_name)
            return f"Opening file: {file_name} stack is being updated = {stack}", file_name
        return f"File {file_name} not found.", None

    if "important points " in user_input:
        file_name = user_input.split("important points ", 1)[1].strip()
        if os.path.exists(f"files/{file_name}"):
            important_points = get_important_points(f"files/{file_name}")
            if isinstance(important_points, list) and important_points:
                # Join important points into a response string
                points_response = "\n".join(f"• {point}" for point in important_points)
                return f"Here are the important points from the file:\n{points_response}", None
            return "No important points found or the file is too short to extract meaningful points.", None
        else:
            return "Sorry, the file doesn't exist.", None
    
    if "?" in user_input:
        return """i think you are asking a question to me ..
         maybe search for help and use commands to correctly communicate with the chatbot""",None

    if user_input.startswith("summarize "):
        file_name = user_input.split("summarize ", 1)[1].strip()
        if os.path.exists(f"files/{file_name}"):
            text = extract_text_from_pdf(f"files/{file_name}")
            summary = summarize_text(text)
            return f"Here is the summary:\n{summary}", None
        else:
            return "Sorry, the file doesn't exist.", None
    
    if "help" in user_input:
        return """Hello this is blackberry-chatbot ....
        using a little bit help from my admin - Harry <3
        i can help you a lotttt...
        i am gonna help you by listing all the task that i can do ...
        so i can open files (open filename.extension) ...
        list all the files that are in the files repo fixed by my admin (show me files) ..
        i can summarize the contents of those files (summarize filename.extension) 
        or any content that you give to me (summarize this [content]) ... 
        ask for important points to me by (important points filename.extension)..
        now i can question you by the key word (quiz me on this filename.extension)..
        also i can question you based on the content given by you (quiz me with this [content])
        also i can respond to basic things like hello , bye  and how are you..
        thank you for using blackberry-chatbot over the others""" , None

    if user_input.startswith("quiz me on this "):
        quiz_source = user_input.split("quiz me on this", 1)[1].strip()

        if "." in quiz_source:  # If it's a file
            file_path = os.path.join(FILES_FOLDER, quiz_source)
            if os.path.exists(file_path):
                text = extract_text_from_pdf(file_path)
                finaltext=summarize_text(text)
            else:
                return "Sorry, the file doesn't exist.", None

        user_id = "test_user"  # Replace with a real user session ID if needed
        return start_quiz(user_id, finaltext), None

    if user_input.startswith("quiz me with this"):
        # Extract the custom text that the user wants to summarize
        custom_text = user_input.split("quiz me with this", 1)[1].strip()
        if custom_text:
            text=summarize_text(custom_text)
            user_id = "test_user"  
            return start_quiz(user_id, text), None
        return "please put the right text"

    if user_input.startswith("answer "):
        user_answer = user_input.split("answer ", 1)[1].strip()
        user_id = "test_user"  # Replace with a real user session ID
        return check_answer(user_id, user_answer), None

    for key in responses:
        if key in user_input:
            return random.choice(responses[key]), None
    return random.choice(responses["default"]), None

#_____________________________________________#

@app.route('/')
def index():
    """Render the chatbot interface."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and return a response."""
    user_input = request.form['message']
    bot_response, file_to_open = get_response(user_input)
    return jsonify({'response': bot_response, 'file_to_open': file_to_open})

@app.route('/summarize/<filename>')
def summarize_pdf(filename):
    """Extracts and summarizes text from a PDF file."""
    pdf_path = os.path.join(FILES_FOLDER, filename)
    
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'File not found'}), 404

    extracted_text = extract_text_from_pdf(pdf_path)
    if "Error" in extracted_text:
        return jsonify({'error': extracted_text}), 500

    summary = summarize_text(extracted_text)
    return jsonify({'summary': summary})

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory(FILES_FOLDER, filename)

#_____________________________________________#

if __name__ == '__main__':
    app.run(debug=True) 