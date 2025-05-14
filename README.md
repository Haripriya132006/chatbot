🫐 Blackberry Chatbot
=
Blackberry is a multifunctional chatbot built using Flask, Hugging Face Transformers, spaCy, and PyMuPDF. It supports conversational interaction, PDF summarization, quiz generation from text, and file management features.

🚀 Features
=
🤖 Conversational Bot: Responds to greetings, simple commands, and custom phrases.

📄 PDF Summarization: Extracts and summarizes content from uploaded PDF files using t5-small.

🧠 Quiz Generator: Automatically generates multiple-choice questions from text.

📚 Important Points Extraction: Highlights key points from documents using summarization models.

🗂️ File Explorer: Lists and opens files stored in the files/ directory.

🧾 Memory-Based Summarization: Remembers previously summarized inputs to avoid redundant processing.

🧪 Fallback OCR: Performs OCR if no text is found in a PDF (optional, integrate pytesseract).

🛠️ Tech Stack:
=
Flask - Lightweight web framework for Python

spaCy - NLP for sentence parsing and keyword extraction

Hugging Face Transformers - For summarization (t5-small)

PyMuPDF (fitz) - PDF text extraction

PIL - Image handling (optional)

HTML/CSS/JS - Frontend interactions (for file links)

💬 Supported Commands
show me files — Lists all files in the files/ directory

open filename.pdf — Opens a specified file

summarize filename.pdf — Summarizes a file

summarize this <text> — Summarizes user-provided text

important points filename.pdf — Shows key points from a file

Chat-friendly phrases like hello, bye, love you, etc.

🧪 Example Quiz Flow
=
User inputs a block of text.

Bot extracts key sentences and blanks out words.

Multiple-choice options are generated.

Quiz session tracks score and progress.

🧠 Notes
=
summary.json caches input-output summary pairs.

Stack tracks the history of opened files.

Summarization chunks are capped at ~2000 characters per chunk.

🧾 To Run Locally
=
```
pip install flask transformers spacy PyMuPDF Pillow
python -m spacy download en_core_web_sm
python app.py
```
