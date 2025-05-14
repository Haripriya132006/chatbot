##🫐 Blackberry Chatbot
=
Blackberry is a multifunctional chatbot built using Flask, Hugging Face Transformers, spaCy, and PyMuPDF. It supports conversational interaction, PDF summarization, quiz generation from text, and file management features.

##🚀 Features
=
🤖 Conversational Bot: Responds to greetings, simple commands, and custom phrases.
📄 PDF Summarization: Extracts and summarizes content from uploaded PDF files using t5-small.
🧠 Quiz Generator: Automatically generates multiple-choice questions from text.
📚 Important Points Extraction: Highlights key points from documents using summarization models.
🗂️ File Explorer: Lists and opens files stored in the files/ directory.
🧾 Memory-Based Summarization: Remembers previously summarized inputs to avoid redundant processing.
🧪 Fallback OCR: Performs OCR if no text is found in a PDF (optional, integrate pytesseract).

##🛠️ Tech Stack:
=
Flask - Lightweight web framework for Python
spaCy - NLP for sentence parsing and keyword extraction
Hugging Face Transformers - For summarization (t5-small)
PyMuPDF (fitz) - PDF text extraction
PIL - Image handling (optional)
HTML/CSS/JS - Frontend interactions (for file links)

