import io
import re
from typing import List, Dict, Any


def extract_text_from_file(uploaded_file) -> str:
    """Extract raw string text from either a .docx or .pdf file."""
    name = uploaded_file.name.lower()

    if name.endswith('.docx'):
        import docx
        doc = docx.Document(uploaded_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)

    elif name.endswith('.pdf'):
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)

    # Fallback plain text / markdown
    content = uploaded_file.read()
    if isinstance(content, bytes):
        return content.decode('utf-8', errors='ignore')
    return str(content)


def parse_mcq_document(uploaded_file) -> List[Dict[str, Any]]:
    """
    Parses an uploaded .docx or .pdf document containing MCQs.
    Recognizes patterns for Question, Options A-D, Answer key, and Explanation.
    """
    text = extract_text_from_file(uploaded_file)
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')

    # Split text into separate question blocks (e.g., "1.", "Q1.", "Question 1:")
    block_delimiter = r'\n(?=(?:Q|Question)?\s*\d+[\.\:\)])'
    raw_blocks = re.split(block_delimiter, '\n' + normalized, flags=re.IGNORECASE)

    parsed_questions = []
    auto_order = 1

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        # 1. Extract Question Text
        q_match = re.search(r'^(?:(?:Q|Question)?\s*(\d+)[\.\:\)]\s*)?(.*?)(?=(?:\n\s*[A-D][\.\:\)]|\Z))', block, flags=re.DOTALL | re.IGNORECASE)
        if not q_match:
            continue

        explicit_order = q_match.group(1)
        q_text = q_match.group(2).strip()
        order_val = int(explicit_order) if explicit_order and explicit_order.isdigit() else auto_order

        # 2. Extract Options A, B, C, D
        opt_a_match = re.search(r'\n\s*A[\.\:\)]\s*(.*?)(?=(?:\n\s*B[\.\:\)]|\Z))', block, flags=re.DOTALL | re.IGNORECASE)
        opt_b_match = re.search(r'\n\s*B[\.\:\)]\s*(.*?)(?=(?:\n\s*C[\.\:\)]|\Z))', block, flags=re.DOTALL | re.IGNORECASE)
        opt_c_match = re.search(r'\n\s*C[\.\:\)]\s*(.*?)(?=(?:\n\s*D[\.\:\)]|\Z))', block, flags=re.DOTALL | re.IGNORECASE)
        opt_d_match = re.search(r'\n\s*D[\.\:\)]\s*(.*?)(?=(?:\n\s*(?:Ans|Answer|Correct|Key|Explanation|Rationale)[\.\:\)]?|\Z))', block, flags=re.DOTALL | re.IGNORECASE)

        opt_a = opt_a_match.group(1).strip() if opt_a_match else ""
        opt_b = opt_b_match.group(1).strip() if opt_b_match else ""
        opt_c = opt_c_match.group(1).strip() if opt_c_match else ""
        opt_d = opt_d_match.group(1).strip() if opt_d_match else ""

        # Only process as an MCQ if at least Options A and B exist
        if not (opt_a and opt_b):
            continue

        # 3. Extract Correct Option Letter
        ans_match = re.search(r'(?:Ans|Answer|Correct Answer|Correct|Key)[\s\:\-\)]*([A-D])\b', block, flags=re.IGNORECASE)
        correct_letter = ans_match.group(1).upper() if ans_match else 'A'

        # 4. Extract Explanation / Rationale
        expl_match = re.search(r'(?:Explanation|Rationale|Rubric|Note)[\s\:\-\)]*(.*?)$', block, flags=re.DOTALL | re.IGNORECASE)
        explanation = expl_match.group(1).strip() if expl_match else ""

        parsed_questions.append({
            'order': order_val,
            'question_text': q_text,
            'option_a': opt_a,
            'option_b': opt_b,
            'option_c': opt_c,
            'option_d': opt_d,
            'correct_option': correct_letter,
            'explanation': explanation,
        })
        auto_order += 1

    return parsed_questions