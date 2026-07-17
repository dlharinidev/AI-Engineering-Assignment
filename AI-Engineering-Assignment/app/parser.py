import hashlib
import uuid
import re
import os

class DocumentParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def compute_hash(self, heading: str, content: str):
        # Hash heading and content together
        text = f"{heading}\n{content}".strip()
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def identify_level(self, text: str):
        """
        Identify hierarchy level of a line:
        Level 0: Document Title (All Caps)
        Level 1: Section (e.g., 1.0 Introduction)
        Level 2: Subsection (e.g., 1.1 Safety)
        """
        text = text.strip()
        if not text:
            return None
        
        # Check for Section/Subsection numbering (e.g., 1.0 Introduction, 2.1.3 Battery)
        # Level 1 matches: 1.0, 2.0, etc.
        # Level 2 matches: 2.1, 3.2.1, etc.
        match = re.match(r'^(\d+)\.(\d+)(?:\.(\d+))*\s+(.*)', text)
        if match:
            major, minor = match.group(1), match.group(2)
            if minor == "0":
                return 1
            else:
                return 2
        
        # Check for All Caps Title (e.g., CARDIOTRACK CT-200...)
        if text.isupper() and len(text) > 10:
            return 0
            
        return None

    def extract_text_ocr(self):
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            # This will raise an exception if poppler or tesseract are missing
            pages = convert_from_path(self.pdf_path)
            text_parts = []
            for page in pages:
                text_parts.append(pytesseract.image_to_string(page))
            return "\n\n".join(text_parts)
        except Exception as e:
            # OCR failed (binary not found, etc.)
            return None

    def extract_text_pypdf(self):
        import pypdf
        reader = pypdf.PdfReader(self.pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    def parse(self, document_id: int):
        # 1. Extract text using hybrid approach (OCR first, fallback to pypdf)
        text = self.extract_text_ocr()
        if not text:
            text = self.extract_text_pypdf()
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        nodes_data = []
        active_nodes = { 0: None, 1: None, 2: None } # level -> index in nodes_data
        
        for line in lines:
            # Ignore headers/footers/page numbers
            if re.match(r'^\d+$', line) or line.lower().startswith('page'):
                continue
                
            level = self.identify_level(line)
            
            if level is not None:
                # Create a new heading node
                node_idx = len(nodes_data)
                
                # Determine parent
                parent_idx = None
                if level > 0:
                    parent_idx = active_nodes.get(level - 1)
                    if parent_idx is None and level == 2:
                        # Fallback to level 0 parent if level 1 is missing
                        parent_idx = active_nodes.get(0)
                
                nodes_data.append({
                    "heading": line,
                    "content": "",
                    "level": level,
                    "parent_idx": parent_idx,
                    "content_hash": ""
                })
                
                active_nodes[level] = node_idx
                # Reset lower levels
                for l in range(level + 1, 3):
                    active_nodes[l] = None
            else:
                # Body text. Append to the current active node.
                # Find the deepest active node
                active_node_idx = None
                for l in [2, 1, 0]:
                    if active_nodes[l] is not None:
                        active_node_idx = active_nodes[l]
                        break
                        
                if active_node_idx is not None:
                    curr_content = nodes_data[active_node_idx]["content"]
                    if curr_content:
                        nodes_data[active_node_idx]["content"] = curr_content + "\n" + line
                    else:
                        nodes_data[active_node_idx]["content"] = line
        
        # Calculate hashes
        for nd in nodes_data:
            nd["content_hash"] = self.compute_hash(nd["heading"], nd["content"])
            
        return nodes_data