import re
from pathlib import Path
from pypdf import PdfReader

class DocumentParser:
    """Handles extraction and cleaning of text from various document formats."""
    
    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """Extract text from a PDF, TXT, or Markdown file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return DocumentParser._extract_from_pdf(path)
        elif suffix in [".txt", ".md"]:
            return DocumentParser._extract_from_txt(path)
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")

    @staticmethod
    def _extract_from_pdf(path: Path) -> str:
        """Extract text from a PDF using pypdf."""
        reader = PdfReader(path)
        text = [page.extract_text() for page in reader.pages]
        return DocumentParser.clean_text("\n".join(text))

    @staticmethod
    def _extract_from_txt(path: Path) -> str:
        """Extract text from a plain text or markdown file."""
        with open(path, "r", encoding="utf-8") as f:
            return DocumentParser.clean_text(f.read())

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text by standardizing whitespace."""
        # Replace multiple spaces/newlines with a single space or newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()
