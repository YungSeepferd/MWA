"""
PDF-based contact extraction.

This module provides functionality to extract contact information
from PDF documents using PyMuPDF and pdfplumber.
"""

import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from urllib.parse import urlparse

import fitz  # PyMuPDF
import pdfplumber

from .extractor import ContactExtractor
from .models import Contact, ContactMethod, ConfidenceLevel, DiscoveryContext
from ..config.settings import Settings

@dataclass
class ExtractedContact:
    """
    Represents a contact extracted from a PDF.
    
    Attributes:
        source: Source PDF file path or URL
        contact: The extracted contact information
        context: Additional context for extraction
        raw_data: Raw PDF data and processing information
        extraction_metadata: Metadata about the extraction process
    """
    source: str
    contact: Contact
    context: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source,
            "contact": self.contact.to_dict(),
            "context": self.context,
            "raw_data": self.raw_data,
            "extraction_metadata": self.extraction_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedContact":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            contact=Contact.from_dict(data["contact"]),
            context=data.get("context", {}),
            raw_data=data.get("raw_data", {}),
            extraction_metadata=data.get("extraction_metadata", {})
        )

logger = logging.getLogger(__name__)

class PDFExtractor(ContactExtractor):
    """
    Extracts contact information from PDF documents.
    
    Supports both digital and scanned PDFs with text extraction,
    table parsing, and metadata analysis.
    """
    
    def __init__(
        self,
        config: Settings,
        max_file_size_mb: int = 10,
        extract_tables: bool = True,
        extract_metadata: bool = True,
        confidence_threshold: float = 0.7,
        ocr_fallback: bool = True
    ):
        """
        Initialize PDF extractor.
        
        Args:
            config: Settings object
            max_file_size_mb: Maximum PDF file size to process (MB)
            extract_tables: Whether to extract tables from PDFs
            extract_metadata: Whether to extract PDF metadata
            confidence_threshold: Minimum confidence score for extracted contacts
            ocr_fallback: Whether to use OCR for scanned PDFs
        """
        super().__init__(config)
        self.max_file_size_mb = max_file_size_mb
        self.extract_tables = extract_tables
        self.extract_metadata = extract_metadata
        self.confidence_threshold = confidence_threshold
        self.ocr_fallback = ocr_fallback
        
        # Initialize OCR extractor for fallback
        if ocr_fallback:
            try:
                from .ocr_extractor import OCRExtractor
                self.ocr_extractor = OCRExtractor(config=config)
            except ImportError:
                logger.warning("OCR extractor not available. Scanned PDF support disabled.")
                self.ocr_extractor = None
        else:
            self.ocr_extractor = None
    
    def can_process(self, source: Union[str, Path, bytes]) -> bool:
        """
        Check if the source can be processed by this extractor.
        
        Args:
            source: PDF URL, file path, or PDF data
            
        Returns:
            True if the source is a PDF that can be processed
        """
        if isinstance(source, str):
            # Check if it's a URL or file path
            if source.startswith(('http://', 'https://')):
                # Check file extension
                parsed = urlparse(source)
                ext = Path(parsed.path).suffix.lower()
                return ext == '.pdf'
            else:
                # Check if file exists and is a PDF
                path = Path(source)
                return path.exists() and path.suffix.lower() == '.pdf'
        elif isinstance(source, Path):
            return source.suffix.lower() == '.pdf'
        elif isinstance(source, bytes):
            # Check PDF magic bytes
            return source.startswith(b'%PDF')
        return False
    
    def extract_contacts(
        self,
        source: Union[str, Path, bytes],
        context: Optional[Dict] = None
    ) -> List[ExtractedContact]:
        """
        Extract contacts from a PDF document.
        
        Args:
            source: PDF URL, file path, or PDF data
            context: Additional context for extraction
            
        Returns:
            List of extracted contacts with confidence scores
        """
        try:
            # Check file size if it's a file
            if isinstance(source, (str, Path)) and not str(source).startswith(('http://', 'https://')):
                file_size_mb = Path(source).stat().st_size / (1024 * 1024)
                if file_size_mb > self.max_file_size_mb:
                    logger.warning(f"PDF file too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
                    return []
            
            # Load PDF
            pdf_document = self._load_pdf(source)
            if pdf_document is None:
                return []
            
            # Extract text from PDF
            text = self._extract_text(pdf_document)
            if not text:
                logger.debug("No text extracted from PDF")
                
                # Try OCR fallback for scanned PDFs
                if self.ocr_fallback and self.ocr_extractor:
                    logger.info("Attempting OCR fallback for scanned PDF")
                    return self._extract_with_ocr(pdf_document, source, context)
                
                return []
            
            logger.debug(f"Extracted text from PDF: {text[:200]}...")
            
            # Extract contacts from text
            contacts = self._extract_contacts_from_text(text, source, context)
            
            # Extract from tables if enabled
            if self.extract_tables:
                table_contacts = self._extract_from_tables(pdf_document, source, context)
                contacts.extend(table_contacts)
            
            # Extract from metadata if enabled
            if self.extract_metadata:
                metadata_contacts = self._extract_from_metadata(pdf_document, source, context)
                contacts.extend(metadata_contacts)
            
            # Score contacts based on extraction quality
            scored_contacts = self._score_contacts(contacts, pdf_document, text)
            
            # Filter by confidence threshold
            filtered_contacts = [
                contact for contact in scored_contacts
                if self._convert_confidence_level(contact.contact.confidence) >= self.confidence_threshold
            ]
            
            logger.info(f"Extracted {len(filtered_contacts)} contacts from PDF")
            return filtered_contacts
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return []
    
    def _load_pdf(self, source: Union[str, Path, bytes]) -> Optional[fitz.Document]:
        """Load PDF from various sources."""
        try:
            if isinstance(source, str):
                if source.startswith(('http://', 'https://')):
                    # Download PDF from URL
                    import requests
                    response = requests.get(source, timeout=30)
                    response.raise_for_status()
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = tmp_file.name
                    
                    # Load from temporary file
                    pdf_document = fitz.open(tmp_path)
                    
                    # Clean up temp file
                    Path(tmp_path).unlink()
                    
                    return pdf_document
                else:
                    # Load from file path
                    return fitz.open(source)
            elif isinstance(source, Path):
                return fitz.open(str(source))
            elif isinstance(source, bytes):
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(source)
                    tmp_path = tmp_file.name
                
                # Load from temporary file
                pdf_document = fitz.open(tmp_path)
                
                # Clean up temp file
                Path(tmp_path).unlink()
                
                return pdf_document
            else:
                logger.error(f"Unsupported source type: {type(source)}")
                return None
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return None
    
    def _extract_text(self, pdf_document: fitz.Document) -> str:
        """Extract text from PDF using PyMuPDF."""
        try:
            text_parts = []
            
            # Extract text from each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    text_parts.append(page_text)
            
            return '\n'.join(text_parts)
            
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _extract_contacts_from_text(
        self,
        text: str,
        source: Union[str, Path, bytes],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from PDF text using pattern matching."""
        contacts = []
        
        # Extract emails
        emails = self._extract_emails(text)
        for email, confidence in emails:
            contact = Contact(
                method=ContactMethod.EMAIL,
                value=email,
                confidence=confidence,
                source_url=str(source),
                metadata={"pdf_extracted": True}
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, email)}
            )
            contacts.append(extracted)
        
        # Extract phone numbers
        phones = self._extract_phones(text)
        for phone, confidence in phones:
            contact = Contact(
                method=ContactMethod.PHONE,
                value=phone,
                confidence=confidence,
                source_url=str(source),
                metadata={"pdf_extracted": True}
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, phone)}
            )
            contacts.append(extracted)
        
        # Extract forms
        forms = self._extract_forms(text)
        for form_url, confidence in forms:
            contact = Contact(
                method=ContactMethod.FORM,
                value=form_url,
                confidence=confidence,
                source_url=str(source),
                metadata={"pdf_extracted": True}
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, form_url)}
            )
            contacts.append(extracted)
        
        return contacts
    
    def _extract_from_tables(
        self,
        pdf_document: fitz.Document,
        source: Union[str, Path, bytes],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from PDF tables."""
        if not self.extract_tables:
            return []
        
        contacts = []
        
        try:
            # Save PDF to temporary file for pdfplumber
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_document.tobytes())
                tmp_path = tmp_file.name
            
            # Open with pdfplumber for table extraction
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    # Extract tables
                    tables = page.extract_tables()
                    
                    for table in tables:
                        # Convert table to text for processing
                        table_text = self._table_to_text(table)
                        
                        # Extract contacts from table text
                        table_contacts = self._extract_contacts_from_text(
                            table_text,
                            source,
                            {**context, "source_type": "table"} if context else {"source_type": "table"}
                        )
                        
                        # Boost confidence for table-extracted contacts
                        for contact in table_contacts:
                            # Tables often contain structured contact info
                            current_conf = self._convert_confidence_level(contact.contact.confidence)
                            boosted_conf = min(1.0, current_conf * 1.2)
                            contact.contact.confidence = self._convert_to_confidence_level(boosted_conf)
                        
                        contacts.extend(table_contacts)
            
            # Clean up temp file
            Path(tmp_path).unlink()
            
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return contacts
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table data to text for processing."""
        text_parts = []
        
        for row in table:
            if row:
                # Clean up row data
                cleaned_row = [cell.strip() if cell else "" for cell in row]
                # Join non-empty cells
                row_text = " | ".join(filter(None, cleaned_row))
                if row_text:
                    text_parts.append(row_text)
        
        return "\n".join(text_parts)
    
    def _extract_from_metadata(
        self,
        pdf_document: fitz.Document,
        source: Union[str, Path, bytes],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from PDF metadata."""
        if not self.extract_metadata:
            return []
        
        contacts = []
        
        try:
            metadata = pdf_document.metadata
            
            if metadata:
                # Extract from author field
                if metadata.get('author'):
                    author_contacts = self._extract_contacts_from_text(
                        metadata['author'],
                        source,
                        {**context, "source_type": "metadata"} if context else {"source_type": "metadata"}
                    )
                    contacts.extend(author_contacts)
                
                # Extract from creator field
                if metadata.get('creator'):
                    creator_contacts = self._extract_contacts_from_text(
                        metadata['creator'],
                        source,
                        {**context, "source_type": "metadata"} if context else {"source_type": "metadata"}
                    )
                    contacts.extend(creator_contacts)
                
                # Extract from title field
                if metadata.get('title'):
                    title_contacts = self._extract_contacts_from_text(
                        metadata['title'],
                        source,
                        {**context, "source_type": "metadata"} if context else {"source_type": "metadata"}
                    )
                    contacts.extend(title_contacts)
                
                # Extract from subject field
                if metadata.get('subject'):
                    subject_contacts = self._extract_contacts_from_text(
                        metadata['subject'],
                        source,
                        {**context, "source_type": "metadata"} if context else {"source_type": "metadata"}
                    )
                    contacts.extend(subject_contacts)
        
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
        
        return contacts
    
    def _extract_with_ocr(
        self,
        pdf_document: fitz.Document,
        source: Union[str, Path, bytes],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from PDF using OCR fallback."""
        if not self.ocr_extractor:
            return []
        
        contacts = []
        
        try:
            # Convert each page to image and extract text with OCR
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page as image
                pix = page.get_pixmap(dpi=300)  # High resolution for OCR
                img_data = pix.tobytes("png")
                
                # Extract contacts with OCR
                page_contacts = self.ocr_extractor.extract_contacts(
                    img_data,
                    {**context, "page": page_num} if context else {"page": page_num}
                )
                
                # Adjust source to indicate OCR extraction
                for contact in page_contacts:
                    contact.source = f"{source}#page={page_num}#ocr"
                
                contacts.extend(page_contacts)
        
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
        
        return contacts
    
    def _extract_emails(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract email addresses from text."""
        emails = []
        
        # Pattern for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Also handle obfuscated emails
        obfuscated_patterns = [
            (r'\b[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\s*\[\s*dot\s*\]\s*[A-Z|a-z]{2,}\b', self._deobfuscate_email),
            (r'\b[A-Za-z0-9._%+-]+\s*\(\s*at\s*\)\s*[A-Za-z0-9.-]+\s*\(\s*dot\s*\)\s*[A-Z|a-z]{2,}\b', self._deobfuscate_email),
        ]
        
        # Extract normal emails
        for match in re.finditer(email_pattern, text):
            email = match.group()
            if self._validate_email(email):
                emails.append((email, ConfidenceLevel.HIGH))
        
        # Extract obfuscated emails
        for pattern, deobfuscator in obfuscated_patterns:
            for match in re.finditer(pattern, text):
                obfuscated = match.group()
                email = deobfuscator(obfuscated)
                if self._validate_email(email):
                    emails.append((email, ConfidenceLevel.MEDIUM))
        
        return emails
    
    def _extract_phones(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract phone numbers from text."""
        phones = []
        
        # Patterns for German and international phone numbers
        patterns = [
            # German format
            r'\b(?:\+49|0049|0)\s*[1-9]\d{1,4}\s*\d{1,14}(?:\s*\d{1,14})?\b',
            # International format
            r'\b(?:\+|00)\d{1,4}\s*\d{1,14}(?:\s*\d{1,14})?\b',
            # Local format (Munich)
            r'\b089\s*\d{1,14}(?:\s*\d{1,14})?\b',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                phone = match.group()
                if self._validate_phone(phone):
                    # Score based on format completeness
                    if phone.startswith('+') or phone.startswith('00'):
                        confidence = ConfidenceLevel.HIGH
                    elif '089' in phone:  # Munich area code
                        confidence = ConfidenceLevel.HIGH
                    else:
                        confidence = ConfidenceLevel.MEDIUM
                    
                    phones.append((phone, confidence))
        
        return phones
    
    def _extract_forms(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract form URLs from text."""
        forms = []
        
        # Look for form-related keywords and URLs
        form_keywords = ['formular', 'anfrage', 'kontakt', 'bewerbung', 'anmeldung']
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        
        # Find URLs near form keywords
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains form keywords
            if any(keyword in line_lower for keyword in form_keywords):
                # Look for URLs in this line or nearby lines
                search_window = lines[max(0, i-1):min(len(lines), i+2)]
                search_text = ' '.join(search_window)
                
                for match in re.finditer(url_pattern, search_text):
                    url = match.group()
                    # Validate URL
                    if self._validate_url(url):
                        # Score based on proximity to form keywords
                        if any(keyword in line_lower for keyword in form_keywords):
                            confidence = ConfidenceLevel.HIGH
                        else:
                            confidence = ConfidenceLevel.MEDIUM
                        
                        forms.append((url, confidence))
        
        return forms
    
    def _deobfuscate_email(self, obfuscated: str) -> str:
        """Convert obfuscated email to normal format."""
        # Replace [at] or (at) with @
        email = re.sub(r'\s*\[\s*at\s*\]\s*|\s*\(\s*at\s*\)\s*', '@', obfuscated, flags=re.IGNORECASE)
        # Replace [dot] or (dot) with .
        email = re.sub(r'\s*\[\s*dot\s*\]\s*|\s*\(\s*dot\s*\)\s*', '.', email, flags=re.IGNORECASE)
        # Remove any remaining spaces
        email = email.replace(' ', '')
        return email
    
    def _get_text_snippet(self, text: str, keyword: str, window: int = 50) -> str:
        """Get text snippet around a keyword."""
        try:
            index = text.index(keyword)
            start = max(0, index - window)
            end = min(len(text), index + len(keyword) + window)
            return text[start:end]
        except ValueError:
            return ""
    
    def _score_contacts(
        self,
        contacts: List[ExtractedContact],
        pdf_document: fitz.Document,
        text: str
    ) -> List[ExtractedContact]:
        """Score contacts based on extraction quality."""
        # Calculate text quality
        text_quality = self._calculate_text_quality(text)
        
        # Adjust contact scores based on quality metrics
        scored_contacts = []
        for contact in contacts:
            # Base confidence from pattern matching
            base_confidence = self._convert_confidence_level(contact.contact.confidence)
            
            # Adjust based on text quality
            final_confidence = min(1.0, base_confidence * text_quality)
            
            # Update contact confidence
            contact.contact.confidence = self._convert_to_confidence_level(final_confidence)
            scored_contacts.append(contact)
        
        return scored_contacts
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate text quality score (0-1)."""
        if not text:
            return 0.0
        
        # Calculate character diversity (avoid repetitive garbage)
        unique_chars = len(set(text))
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        char_diversity = unique_chars / total_chars
        
        # Check for common OCR errors
        ocr_errors = len(re.findall(r'[^\w\s@+.\-(),:/]', text)) / total_chars
        
        # Calculate word coherence (ratio of words to total tokens)
        words = len(re.findall(r'\b\w+\b', text))
        quality_score = (char_diversity + (1 - ocr_errors) + min(1.0, words / 10)) / 3
        
        return max(0.1, min(1.0, quality_score))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it has enough digits
        digits = len(re.findall(r'\d', clean_phone))
        return digits >= 6  # Minimum 6 digits for a valid phone number
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _convert_confidence_level(self, confidence: ConfidenceLevel) -> float:
        """Convert ConfidenceLevel enum to numeric value."""
        mapping = {
            ConfidenceLevel.HIGH: 0.9,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.3
        }
        return mapping.get(confidence, 0.5)
    
    def _convert_to_confidence_level(self, confidence_value: float) -> ConfidenceLevel:
        """Convert numeric confidence value to ConfidenceLevel enum."""
        if confidence_value >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_value >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


# Example usage
if __name__ == "__main__":
    # Initialize PDF extractor
    extractor = PDFExtractor(
        max_file_size_mb=10,
        extract_tables=True,
        extract_metadata=True,
        confidence_threshold=0.6
    )
    
    # Test with a sample PDF
    test_pdf = "path/to/contact_brochure.pdf"
    
    if extractor.can_process(test_pdf):
        contacts = extractor.extract_contacts(test_pdf)
        
        for contact in contacts:
            print(f"Found {contact.contact.method}: {contact.contact.value} "
                  f"(confidence: {contact.contact.confidence.name})")
    else:
        print("Cannot process the provided PDF")