\# Tri9T AI Engineering Assignment - CT-200 Parser



This system ingests technical manuals, builds a hierarchical tree using OCR, detects changes across versions, and uses an LLM to generate QA test cases.



\## Tech Stack

\- \*\*Backend:\*\* FastAPI, SQLAlchemy (SQLite), Pydantic

\- \*\*OCR:\*\* Tesseract, pdf2image

\- \*\*Database:\*\* SQLite (Relational), MongoDB (LLM cache)

\- \*\*LLM:\*\* OpenAI GPT-3.5/4



\## Setup Instructions



1\. \*\*Install System Dependencies:\*\*

&#x20;  - Install Tesseract OCR: `sudo apt install tesseract-ocr` (Ubuntu) or `brew install tesseract` (Mac)

&#x20;  - Install Poppler: `sudo apt install poppler-utils`



2\. \*\*Python Environment:\*\*

&#x20;  ```bash

&#x20;  pip install -r requirements.txt

