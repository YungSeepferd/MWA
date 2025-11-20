# Contact Discovery System Documentation

## Overview
This document describes the MAFA Contact Discovery System, which is responsible for extracting, validating, and managing contact information from real estate listings. The system combines multiple extraction methods, validation algorithms, and quality assessment techniques to provide reliable contact data.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Discovery Team  
**Estimated Reading Time:** 35-40 minutes

---

## System Architecture

### Discovery Workflow Overview
```
┌─────────────────────────────────────────────────────────────┐
│                   Contact Discovery Pipeline                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Data       │  │  Contact    │  │   Quality   │
│ Acquisition  │  │ Extraction  │  │ Assessment  │
│              │  │             │  │             │
│ - Web        │  │ - OCR       │  │ - Confidence│
│   Scraping   │  │ - PDF       │  │ - Validation│
│ - APIs       │  │ - API       │  │ - Deduplication│
│ - Manual     │  │ - Manual    │  │ - Scoring   │
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Data       │  │  Storage    │  │ Notification │
│ Enrichment   │  │  & Index    │  │ & Alerting   │
│              │  │             │  │             │
│ - Validation │  │ - Database  │  │ - User       │
│ - Normalization│ │ - Cache     │  │   Updates    │
│ - Enhancement│  │ - Search    │  │ - Dashboard  │
└──────────────┘  └─────────────┘  └─────────────┘
```

### Core Components

#### 1. Data Acquisition Layer
- **Web Scrapers**: Extract data from real estate websites
- **API Connectors**: Retrieve data from provider APIs
- **Manual Input**: Human-entered contact information
- **File Processors**: Handle uploaded documents and PDFs

#### 2. Extraction Engine
- **OCR Service**: Text extraction from images
- **PDF Parser**: Document content extraction
- **Pattern Recognition**: Contact information identification
- **Natural Language Processing**: Contextual extraction

#### 3. Validation System
- **Format Validation**: Phone, email, address validation
- **Cross-Reference Validation**: Database consistency checks
- **Human Verification**: Manual review workflows
- **Quality Scoring**: Automated quality assessment

#### 4. Storage & Indexing
- **Database Storage**: Persistent contact storage
- **Search Indexing**: Fast contact retrieval
- **Version Control**: Contact change tracking
- **Backup Systems**: Data protection and recovery

---

## Contact Extraction Methods

### OCR-Based Extraction
```python
# mfa/contact_discovery/ocr_extractor.py
import cv2
import pytesseract
from PIL import Image, ImageEnhance
from typing import List, Dict, Any, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class OCRContactExtractor:
    """Contact extraction using Optical Character Recognition."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.phone_patterns = [
            r'(\+49\s?0?\d{1,4}[\s-]?\d{3,}[\s-]?\d{3,})',  # German numbers
            r'(0\d{1,4}[\s-]?\d{3,}[\s-]?\d{3,})',          # Domestic format
            r'(\+?\d{1,3}[\s-]?\d{8,})'                     # International
        ]
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
    def extract_contacts_from_image(self, image_path: str, 
                                   language: str = 'deu') -> Dict[str, Any]:
        """Extract contact information from an image."""
        try:
            # Load and preprocess image
            image = self._preprocess_image(image_path)
            
            # Extract text using OCR
            text_data = pytesseract.image_to_data(
                image, 
                lang=language, 
                output_type=pytesseract.Output.DICT
            )
            
            # Process extracted text
            contacts = self._process_ocr_data(text_data)
            
            # Validate and score contacts
            validated_contacts = self._validate_extracted_contacts(contacts)
            
            return {
                'success': True,
                'extracted_contacts': validated_contacts,
                'confidence_score': self._calculate_overall_confidence(validated_contacts),
                'processing_metadata': {
                    'language': language,
                    'image_size': image.size,
                    'text_regions': len([t for t in text_data['text'] if t.strip()])
                }
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extracted_contacts': []
            }
    
    def _preprocess_image(self, image_path: str) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        # Load image
        image = Image.open(image_path)
        
        # Convert to grayscale if needed
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize if too large
        max_size = (2000, 2000)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Denoise
        image_array = cv2.cvtColor(
            cv2.imread(image_path), 
            cv2.COLOR_RGB2GRAY
        )
        denoised = cv2.fastNlMeansDenoising(image_array)
        image = Image.fromarray(denoised)
        
        return image
    
    def _process_ocr_data(self, text_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """Process OCR text data to extract contacts."""
        contacts = []
        
        # Combine text lines
        lines = self._group_text_by_lines(text_data)
        
        for line_data in lines:
            line_text = line_data['text'].strip()
            
            # Extract phone numbers
            phones = self._extract_phone_numbers(line_text)
            for phone in phones:
                contacts.append({
                    'type': 'phone',
                    'value': phone['number'],
                    'confidence': phone['confidence'],
                    'context': line_data.get('context', ''),
                    'position': line_data.get('position', {}),
                    'extraction_method': 'ocr'
                })
            
            # Extract email addresses
            emails = self._extract_email_addresses(line_text)
            for email in emails:
                contacts.append({
                    'type': 'email',
                    'value': email,
                    'confidence': 0.9,  # High confidence for regex matches
                    'context': line_data.get('context', ''),
                    'position': line_data.get('position', {}),
                    'extraction_method': 'ocr'
                })
        
        return contacts
    
    def _group_text_by_lines(self, text_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """Group OCR data by text lines."""
        lines = {}
        
        for i, text in enumerate(text_data['text']):
            if not text.strip():
                continue
                
            line_num = text_data['line_num'][i]
            if line_num not in lines:
                lines[line_num] = {
                    'text': '',
                    'words': [],
                    'position': {
                        'left': text_data['left'][i],
                        'top': text_data['top'][i],
                        'width': text_data['width'][i],
                        'height': text_data['height'][i]
                    }
                }
            
            lines[line_num]['text'] += text + ' '
            lines[line_num]['words'].append({
                'text': text,
                'confidence': text_data['conf'][i],
                'position': {
                    'left': text_data['left'][i],
                    'top': text_data['top'][i],
                    'width': text_data['width'][i],
                    'height': text_data['height'][i]
                }
            })
        
        # Clean up text and add context
        for line_num, line_data in lines.items():
            line_data['text'] = line_data['text'].strip()
            line_data['confidence'] = sum(
                w['confidence'] for w in line_data['words']
            ) / len(line_data['words'])
        
        return list(lines.values())
    
    def _extract_phone_numbers(self, text: str) -> List[Dict[str, Any]]:
        """Extract phone numbers from text."""
        phones = []
        
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                phone_number = match.group(1)
                
                # Basic validation
                if self._is_valid_phone_number(phone_number):
                    # Calculate confidence based on pattern match
                    confidence = 0.8 if '+49' in phone_number else 0.7
                    
                    phones.append({
                        'number': phone_number,
                        'confidence': confidence,
                        'match_type': 'regex_pattern'
                    })
        
        return phones
    
    def _extract_email_addresses(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        emails = re.findall(self.email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    def _is_valid_phone_number(self, phone: str) -> bool:
        """Basic validation for phone numbers."""
        # Remove common formatting characters
        clean_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Check length and format
        if not re.match(r'^\+?\d{8,15}$', clean_phone):
            return False
        
        # Avoid false positives (e.g., long sequences without +)
        if len(clean_phone) > 15 and '+' not in clean_phone:
            return False
        
        return True
    
    def _validate_extracted_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter extracted contacts."""
        validated_contacts = []
        
        for contact in contacts:
            # Check confidence threshold
            if contact['confidence'] < self.confidence_threshold:
                continue
            
            # Additional validation based on type
            if contact['type'] == 'phone':
                if not self._is_valid_phone_number(contact['value']):
                    continue
            elif contact['type'] == 'email':
                if not self._is_valid_email(contact['value']):
                    continue
            
            validated_contacts.append(contact)
        
        return validated_contacts
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _calculate_overall_confidence(self, contacts: List[Dict[str, Any]]) -> float:
        """Calculate overall extraction confidence."""
        if not contacts:
            return 0.0
        
        # Weight contacts by type and confidence
        weighted_scores = []
        for contact in contacts:
            base_weight = 1.0
            if contact['type'] == 'email':
                base_weight = 1.2  # Emails are more reliable
            elif contact['type'] == 'phone':
                base_weight = 1.0
            
            weighted_scores.append(contact['confidence'] * base_weight)
        
        return sum(weighted_scores) / len(weighted_scores)

# Advanced OCR with multiple languages and optimization
class AdvancedOCRExtractor(OCRContactExtractor):
    """Advanced OCR extractor with multi-language support."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__(confidence_threshold)
        self.language_configs = {
            'deu': {
                'tesseract_lang': 'deu',
                'phone_patterns': [
                    r'(\+49\s?0?\d{1,4}[\s-]?\d{3,}[\s-]?\d{3,})',
                    r'(0\d{1,4}[\s-]?\d{3,}[\s-]?\d{3,})'
                ],
                'contact_keywords': [
                    'telefon', 'tel', 'phone', 'mobil', 'handy',
                    'email', 'e-mail', 'kontakt', 'kontaktperson'
                ]
            },
            'eng': {
                'tesseract_lang': 'eng',
                'phone_patterns': [
                    r'(\+\d{1,3}[\s-]?\d{8,})',
                    r'(\(\d{3}\)\s?\d{3}[\s-]?\d{4})',
                    r'(\d{3}[\s-]?\d{3}[\s-]?\d{4})'
                ],
                'contact_keywords': [
                    'phone', 'telephone', 'mobile', 'cell',
                    'email', 'contact', 'reach'
                ]
            }
        }
    
    def extract_contacts_multi_language(self, image_path: str) -> Dict[str, Any]:
        """Extract contacts using multiple language models."""
        results = {}
        
        # Try extraction with each language
        for lang_code, config in self.language_configs.items():
            try:
                logger.info(f"Attempting OCR extraction with language: {lang_code}")
                
                result = self.extract_contacts_from_image(
                    image_path, 
                    language=config['tesseract_lang']
                )
                
                if result['success']:
                    result['language_used'] = lang_code
                    results[lang_code] = result
                    
            except Exception as e:
                logger.warning(f"OCR failed for language {lang_code}: {str(e)}")
                continue
        
        # Combine and deduplicate results
        if results:
            combined_result = self._combine_multi_language_results(results)
            return combined_result
        
        # Fallback to single language
        return self.extract_contacts_from_image(image_path)
    
    def _combine_multi_language_results(self, language_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Combine results from multiple language extractions."""
        all_contacts = []
        best_confidence = 0.0
        
        for lang_code, result in language_results.items():
            contacts = result.get('extracted_contacts', [])
            
            for contact in contacts:
                contact['language_source'] = lang_code
                all_contacts.append(contact)
            
            if result.get('confidence_score', 0.0) > best_confidence:
                best_confidence = result['confidence_score']
                best_language = lang_code
        
        # Deduplicate contacts
        deduplicated_contacts = self._deduplicate_contacts(all_contacts)
        
        return {
            'success': True,
            'extracted_contacts': deduplicated_contacts,
            'confidence_score': best_confidence,
            'processing_metadata': {
                'languages_used': list(language_results.keys()),
                'best_language': best_language,
                'total_extraction_attempts': len(language_results),
                'deduplication_applied': True
            }
        }
    
    def _deduplicate_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate contacts from multi-language results."""
        seen_values = {}
        unique_contacts = []
        
        for contact in contacts:
            key = f"{contact['type']}:{contact['value'].lower()}"
            
            if key not in seen_values:
                # New contact, add it
                seen_values[key] = contact
                unique_contacts.append(contact)
            else:
                # Duplicate, keep the one with higher confidence
                existing = seen_values[key]
                if contact['confidence'] > existing['confidence']:
                    # Replace with better confidence
                    unique_contacts.remove(existing)
                    unique_contacts.append(contact)
                    seen_values[key] = contact
        
        return unique_contacts
```

### PDF Document Processing
```python
# mfa/contact_discovery/pdf_extractor.py
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class PDFContactExtractor:
    """Contact extraction from PDF documents."""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.contact_patterns = {
            'phone': [
                r'telefon[:\s]*([+0-9\s\-\(\)]{8,})',
                r'tel[:\s]*([+0-9\s\-\(\)]{8,})',
                r'phone[:\s]*([+0-9\s\-\(\)]{8,})',
                r'mobil[:\s]*([+0-9\s\-\(\)]{8,})',
                r'handy[:\s]*([+0-9\s\-\(\)]{8,})',
                r'(?:tel|fon|phone|mobil|handy)\s*[:\-]?\s*([+0-9\s\-\(\)]{8,})'
            ],
            'email': [
                r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'e-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'website': [
                r'website[:\s]*(https?://[^\s]+)',
                r'www\.[^\s]+',
                r'([a-zA-Z0-9.-]+\.(?:com|de|org|net|gov|edu)[^\s]*)'
            ]
        }
    
    def extract_contacts_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract contact information from PDF file."""
        try:
            # Extract text using multiple methods
            pdf_text = self._extract_pdf_text(pdf_path)
            structured_data = self._extract_structured_data(pdf_path)
            
            # Combine text-based and structured extraction
            contacts = []
            
            # Text-based extraction
            text_contacts = self._extract_contacts_from_text(pdf_text)
            contacts.extend(text_contacts)
            
            # Structured data extraction
            if structured_data:
                structured_contacts = self._extract_contacts_from_structured(structured_data)
                contacts.extend(structured_contacts)
            
            # Validate and score contacts
            validated_contacts = self._validate_pdf_contacts(contacts)
            
            return {
                'success': True,
                'extracted_contacts': validated_contacts,
                'confidence_score': self._calculate_pdf_confidence(validated_contacts),
                'processing_metadata': {
                    'pdf_pages': len(pdf_text) if isinstance(pdf_text, list) else 1,
                    'extraction_methods': ['text', 'structured'],
                    'total_text_length': sum(len(page) for page in pdf_text) if isinstance(pdf_text, list) else len(pdf_text)
                }
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'extracted_contacts': []
            }
    
    def _extract_pdf_text(self, pdf_path: str) -> List[str]:
        """Extract text from PDF using multiple methods."""
        text_pages = []
        
        # Method 1: pdfplumber (good for layout-preserving extraction)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_pages.append(text)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}")
        
        # Method 2: PyMuPDF (fitz) - fallback
        if not text_pages:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text:
                        text_pages.append(text)
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {str(e)}")
        
        # Method 3: PyPDF2 - last resort
        if not text_pages:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_pages.append(text)
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {str(e)}")
        
        return text_pages
    
    def _extract_structured_data(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """Extract structured data from PDF (forms, tables, etc.)."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                structured_data = {
                    'forms': [],
                    'tables': [],
                    'annotations': []
                }
                
                # Extract form fields
                for page in pdf.pages:
                    forms = page.forms
                    if forms:
                        structured_data['forms'].extend(forms)
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        structured_data['tables'].extend(tables)
                
                return structured_data if any(structured_data.values()) else None
                
        except Exception as e:
            logger.warning(f"Structured data extraction failed: {str(e)}")
            return None
    
    def _extract_contacts_from_text(self, text_pages: List[str]) -> List[Dict[str, Any]]:
        """Extract contacts from PDF text content."""
        contacts = []
        
        for page_num, page_text in enumerate(text_pages):
            # Combine text with context
            page_contacts = self._process_text_page(page_text, page_num)
            contacts.extend(page_contacts)
        
        return contacts
    
    def _process_text_page(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """Process a single page of text for contact extraction."""
        contacts = []
        
        # Split text into lines for context
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Extract phones
            for pattern in self.contact_patterns['phone']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    phone = match.group(1).strip()
                    if self._is_valid_phone(phone):
                        contacts.append({
                            'type': 'phone',
                            'value': phone,
                            'confidence': 0.85,
                            'context': self._get_line_context(lines, line_num),
                            'page_number': page_num + 1,
                            'line_number': line_num + 1,
                            'extraction_method': 'pdf_text'
                        })
            
            # Extract emails
            for pattern in self.contact_patterns['email']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    email = match.group(1).strip()
                    if self._is_valid_email(email):
                        contacts.append({
                            'type': 'email',
                            'value': email,
                            'confidence': 0.9,
                            'context': self._get_line_context(lines, line_num),
                            'page_number': page_num + 1,
                            'line_number': line_num + 1,
                            'extraction_method': 'pdf_text'
                        })
            
            # Extract websites
            for pattern in self.contact_patterns['website']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    website = match.group(1).strip()
                    contacts.append({
                        'type': 'website',
                        'value': website,
                        'confidence': 0.8,
                        'context': self._get_line_context(lines, line_num),
                        'page_number': page_num + 1,
                        'line_number': line_num + 1,
                        'extraction_method': 'pdf_text'
                    })
        
        return contacts
    
    def _extract_contacts_from_structured(self, structured_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from structured PDF data."""
        contacts = []
        
        # Extract from form fields
        for form in structured_data.get('forms', []):
            form_contacts = self._extract_from_form_fields(form)
            contacts.extend(form_contacts)
        
        # Extract from tables
        for table in structured_data.get('tables', []):
            table_contacts = self._extract_from_table_data(table)
            contacts.extend(table_contacts)
        
        return contacts
    
    def _extract_from_form_fields(self, form: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from PDF form fields."""
        contacts = []
        
        # Access form field properties
        field_name = form.get('fieldname', '').lower()
        field_value = form.get('fieldvalue', '')
        
        if not field_value:
            return contacts
        
        # Identify field type by name
        if any(keyword in field_name for keyword in ['tel', 'phone', 'mobil', 'handy']):
            if self._is_valid_phone(field_value):
                contacts.append({
                    'type': 'phone',
                    'value': field_value,
                    'confidence': 0.95,  # High confidence for form fields
                    'context': f"Form field: {field_name}",
                    'extraction_method': 'pdf_form'
                })
        
        elif any(keyword in field_name for keyword in ['email', 'e-mail']):
            if self._is_valid_email(field_value):
                contacts.append({
                    'type': 'email',
                    'value': field_value,
                    'confidence': 0.95,
                    'context': f"Form field: {field_name}",
                    'extraction_method': 'pdf_form'
                })
        
        elif any(keyword in field_name for keyword in ['website', 'www']):
            contacts.append({
                'type': 'website',
                'value': field_value,
                'confidence': 0.9,
                'context': f"Form field: {field_name}",
                'extraction_method': 'pdf_form'
            })
        
        return contacts
    
    def _extract_from_table_data(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        """Extract contacts from table data."""
        contacts = []
        
        for row_idx, row in enumerate(table):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                
                cell = cell.strip()
                
                # Check each cell for contact patterns
                for contact_type, patterns in self.contact_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, cell, re.IGNORECASE)
                        for match in matches:
                            value = match.group(1).strip() if match.groups() else match.group(0).strip()
                            
                            if contact_type == 'phone' and self._is_valid_phone(value):
                                contacts.append({
                                    'type': 'phone',
                                    'value': value,
                                    'confidence': 0.9,
                                    'context': f"Table cell [{row_idx}, {col_idx}]: {cell[:50]}",
                                    'extraction_method': 'pdf_table'
                                })
                            elif contact_type == 'email' and self._is_valid_email(value):
                                contacts.append({
                                    'type': 'email',
                                    'value': value,
                                    'confidence': 0.9,
                                    'context': f"Table cell [{row_idx}, {col_idx}]: {cell[:50]}",
                                    'extraction_method': 'pdf_table'
                                })
        
        return contacts
    
    def _get_line_context(self, lines: List[str], line_idx: int) -> str:
        """Get context around a specific line."""
        start = max(0, line_idx - 1)
        end = min(len(lines), line_idx + 2)
        context_lines = lines[start:end]
        return ' | '.join(context_lines).strip()
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number."""
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Check length and format
        if not re.match(r'^\+?\d{8,15}$', clean_phone):
            return False
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_pdf_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate extracted PDF contacts."""
        validated = []
        
        for contact in contacts:
            # Check confidence threshold
            if contact['confidence'] < self.confidence_threshold:
                continue
            
            # Deduplicate based on type and value
            is_duplicate = False
            for existing in validated:
                if (existing['type'] == contact['type'] and 
                    existing['value'].lower() == contact['value'].lower()):
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if contact['confidence'] > existing['confidence']:
                        validated.remove(existing)
                        validated.append(contact)
                    break
            
            if not is_duplicate:
                validated.append(contact)
        
        return validated
    
    def _calculate_pdf_confidence(self, contacts: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence for PDF extraction."""
        if not contacts:
            return 0.0
        
        # Weight by contact type and confidence
        type_weights = {
            'email': 1.2,  # More reliable
            'phone': 1.0,
            'website': 0.8
        }
        
        weighted_scores = []
        for contact in contacts:
            weight = type_weights.get(contact['type'], 1.0)
            weighted_scores.append(contact['confidence'] * weight)
        
        return sum(weighted_scores) / len(weighted_scores)
```

### API-Based Contact Extraction
```python# mfa/contact_discovery/api_extractor.py
import requests
from typing import List, Dict, Any, Optional
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ContactExtractor(ABC):
    """Abstract base class for contact extractors."""
    
    @abstractmethod
    def extract_contacts(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from listing data."""
        pass

class APIBasedExtractor(ContactExtractor):
    """Contact extraction using external APIs."""
    
    def __init__(self, api_config: Dict[str, Any]):
        self.api_config = api_config
        self.session = requests.Session()
        self.rate_limit = api_config.get('rate_limit', 60)  # requests per minute
        self.timeout = api_config.get('timeout', 30)
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': 'MAFA-Contact-Discovery/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def extract_contacts(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts using API-based methods."""
        contacts = []
        
        # Extract from structured API data
        api_contacts = self._extract_from_api_data(listing_data)
        contacts.extend(api_contacts)
        
        # Extract from metadata
        metadata_contacts = self._extract_from_metadata(listing_data)
        contacts.extend(metadata_contacts)
        
        # Extract from contact fields
        contact_field_contacts = self._extract_from_contact_fields(listing_data)
        contacts.extend(contact_field_contacts)
        
        return contacts
    
    def _extract_from_api_data(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from structured API response."""
        contacts = []
        
        # Common API response fields for contact information
        contact_fields = [
            'contact_person', 'contact_name', 'owner_name',
            'phone', 'telephone', 'mobil', 'mobile', 'handy',
            'email', 'e_mail', 'mail',
            'website', 'url', 'homepage'
        ]
        
        for field in contact_fields:
            value = listing_data.get(field)
            if not value:
                continue
            
            contact_type = self._determine_contact_type(field, value)
            confidence = self._calculate_api_confidence(field, value)
            
            contacts.append({
                'type': contact_type,
                'value': value,
                'confidence': confidence,
                'context': f"API field: {field}",
                'extraction_method': 'api_structured',
                'source_field': field
            })
        
        return contacts
    
    def _extract_from_metadata(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from metadata fields."""
        contacts = []
        
        # Check metadata and additional_info fields
        metadata_sources = [
            listing_data.get('metadata', {}),
            listing_data.get('additional_info', {}),
            listing_data.get('details', {}),
            listing_data.get('custom_fields', {})
        ]
        
        for metadata in metadata_sources:
            if not isinstance(metadata, dict):
                continue
            
            for key, value in metadata.items():
                if not value or not isinstance(value, str):
                    continue
                
                contact_type = self._determine_contact_type(key, value)
                if contact_type:
                    confidence = self._calculate_api_confidence(key, value)
                    
                    contacts.append({
                        'type': contact_type,
                        'value': value,
                        'confidence': confidence,
                        'context': f"Metadata field: {key}",
                        'extraction_method': 'api_metadata',
                        'source_field': key
                    })
        
        return contacts
    
    def _extract_from_contact_fields(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract from nested contact objects."""
        contacts = []
        
        # Look for nested contact objects
        contact_fields = [
            'contact', 'owner', 'landlord', 'agent', 
            'property_manager', 'contact_person'
        ]
        
        for field_name in contact_fields:
            contact_obj = listing_data.get(field_name)
            if not isinstance(contact_obj, dict):
                continue
            
            # Extract from contact object properties
            for prop_name, prop_value in contact_obj.items():
                if not prop_value or not isinstance(prop_value, str):
                    continue
                
                contact_type = self._determine_contact_type(prop_name, prop_value)
                if contact_type:
                    confidence = self._calculate_api_confidence(prop_name, prop_value)
                    
                    contacts.append({
                        'type': contact_type,
                        'value': prop_value,
                        'confidence': confidence,
                        'context': f"Contact object.{prop_name}",
                        'extraction_method': 'api_contact_object',
                        'source_field': f"{field_name}.{prop_name}"
                    })
        
        return contacts
    
    def _determine_contact_type(self, field_name: str, value: str) -> Optional[str]:
        """Determine contact type from field name and value."""
        field_lower = field_name.lower()
        value_lower = value.lower()
        
        # Phone number patterns
        if any(keyword in field_lower for keyword in ['phone', 'tel', 'mobil', 'mobile', 'handy']):
            if self._is_valid_phone(value):
                return 'phone'
        
        # Email patterns
        if any(keyword in field_lower for keyword in ['email', 'mail', 'e_mail']):
            if self._is_valid_email(value):
                return 'email'
        
        # Website patterns
        if any(keyword in field_lower for keyword in ['website', 'url', 'homepage']):
            if self._is_valid_website(value):
                return 'website'
        
        # Name patterns
        if any(keyword in field_lower for keyword in ['name', 'person', 'owner']):
            if self._is_valid_name(value):
                return 'name'
        
        return None
    
    def _calculate_api_confidence(self, field_name: str, value: str) -> float:
        """Calculate confidence score for API-extracted contacts."""
        field_lower = field_name.lower()
        
        # High confidence for explicit contact fields
        if any(keyword in field_lower for keyword in ['contact', 'phone', 'email', 'tel']):
            return 0.95
        
        # Medium confidence for related fields
        if any(keyword in field_lower for keyword in ['owner', 'manager', 'agent']):
            return 0.8
        
        # Lower confidence for generic fields
        return 0.6
    
    def _is_valid_phone(self, value: str) -> bool:
        """Validate phone number."""
        # Basic phone number validation
        clean_phone = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        return len(clean_phone) >= 8 and clean_phone.replace('+', '').isdigit()
    
    def _is_valid_email(self, value: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, value) is not None
    
    def _is_valid_website(self, value: str) -> bool:
        """Validate website URL."""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, value) is not None
    
    def _is_valid_name(self, value: str) -> bool:
        """Validate name format."""
        # Basic name validation - should have at least 2 characters and mostly letters
        import re
        clean_name = re.sub(r'[^a-zA-ZäöüßÄÖÜß\s\-\.]', '', value)
        return len(clean_name.strip()) >= 2

class ImmoscoutAPIExtractor(APIBasedExtractor):
    """Specialized extractor for Immoscout API."""
    
    def extract_contacts(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from Immoscout API response."""
        contacts = super().extract_contacts(listing_data)
        
        # Immoscout-specific field mappings
        immoscout_contacts = self._extract_immoscout_specific(listing_data)
        contacts.extend(immoscout_contacts)
        
        return contacts
    
    def _extract_immoscout_specific(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract Immoscout-specific contact information."""
        contacts = []
        
        # Immoscout specific fields
        immoscout_fields = {
            'contactPartner': 'name',
            'phoneNumber': 'phone',
            'emailAddress': 'email',
            'companyName': 'company'
        }
        
        for api_field, contact_type in immoscout_fields.items():
            value = listing_data.get(api_field)
            if value:
                contacts.append({
                    'type': contact_type,
                    'value': value,
                    'confidence': 0.9,
                    'context': f"Immoscout API field: {api_field}",
                    'extraction_method': 'immoscout_api',
                    'source_field': api_field
                })
        
        return contacts

class WgGesuchtAPIExtractor(APIBasedExtractor):
    """Specialized extractor for WG-Gesucht API."""
    
    def extract_contacts(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract contacts from WG-Gesucht API response."""
        contacts = super().extract_contacts(listing_data)
        
        # WG-Gesucht specific extraction
        wg_contacts = self._extract_wg_specific(listing_data)
        contacts.extend(wg_contacts)
        
        return contacts
    
    def _extract_wg_specific(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract WG-Gesucht specific contact information."""
        contacts = []
        
        # WG-Gesucht specific fields
        wg_fields = {
            'anbieter': 'name',
            'telefon': 'phone',
            'email': 'email',
            'webseite': 'website'
        }
        
        for wg_field, contact_type in wg_fields.items():
            value = listing_data.get(wg_field)
            if value:
                contacts.append({
                    'type': contact_type,
                    'value': value,
                    'confidence': 0.85,
                    'context': f"WG-Gesucht API field: {wg_field}",
                    'extraction_method': 'wg_gesucht_api',
                    'source_field': wg_field
                })
        
        return contacts
```

---

## Contact Validation System

### Validation Engine
```python
# mfa/contact_discovery/validation.py
from typing import List, Dict, Any, Optional, Tuple
import re
import phonenumbers
from phonenumbers import PhoneNumberType, geocoder
import requests
import dns.resolver
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContactValidator:
    """Comprehensive contact validation system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validation_rules = config.get('validation_rules', {})
        self.external_services = config.get('external_services', {})
        
        # Validation thresholds
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.phone_validation_enabled = config.get('phone_validation', True)
        self.email_validation_enabled = config.get('email_validation', True)
        self.dns_check_enabled = config.get('dns_check', True)
        
    def validate_contacts(self, contacts: List[Dict[str, Any]], 
                         context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Validate a list of contacts."""
        context = context or {}
        validated_contacts = []
        
        for contact in contacts:
            validation_result = self._validate_single_contact(contact, context)
            validated_contacts.append(validation_result)
        
        return validated_contacts
    
    def _validate_single_contact(self, contact: Dict[str, Any], 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single contact."""
        contact_type = contact.get('type')
        value = contact.get('value', '')
        
        # Base validation
        validation_result = {
            'original_contact': contact,
            'validation_status': 'pending',
            'validation_errors': [],
            'validation_warnings': [],
            'confidence_adjustment': 0.0,
            'validation_metadata': {}
        }
        
        if contact_type == 'phone':
            self._validate_phone_contact(contact, validation_result, context)
        elif contact_type == 'email':
            self._validate_email_contact(contact, validation_result, context)
        elif contact_type == 'website':
            self._validate_website_contact(contact, validation_result, context)
        elif contact_type == 'name':
            self._validate_name_contact(contact, validation_result, context)
        
        # Apply validation adjustments
        contact['confidence'] += validation_result['confidence_adjustment']
        contact['validation_status'] = validation_result['validation_status']
        contact['validation_errors'] = validation_result['validation_errors']
        contact['validation_warnings'] = validation_result['validation_warnings']
        contact['validation_metadata'] = validation_result['validation_metadata']
        
        return contact
    
    def _validate_phone_contact(self, contact: Dict[str, Any], 
                              validation_result: Dict[str, Any], 
                              context: Dict[str, Any]) -> None:
        """Validate phone number contact."""
        phone = contact.get('value', '')
        
        # Format validation
        if not self._is_valid_phone_format(phone):
            validation_result['validation_errors'].append('Invalid phone format')
            validation_result['validation_status'] = 'invalid'
            return
        
        # Country-specific validation
        country_code = self._detect_phone_country(phone)
        if country_code:
            validation_result['validation_metadata']['country'] = country_code
            
            # German numbers validation
            if country_code == 'DE':
                self._validate_german_phone(phone, validation_result)
        
        # Real number validation (if enabled)
        if self.phone_validation_enabled:
            self._validate_phone_reality(phone, validation_result)
        
        # Determine final status
        if not validation_result['validation_errors']:
            validation_result['validation_status'] = 'valid'
            validation_result['confidence_adjustment'] = 0.1
        elif validation_result['validation_warnings']:
            validation_result['validation_status'] = 'uncertain'
            validation_result['confidence_adjustment'] = -0.05
        else:
            validation_result['validation_status'] = 'invalid'
            validation_result['confidence_adjustment'] = -0.3
    
    def _validate_email_contact(self, contact: Dict[str, Any], 
                              validation_result: Dict[str, Any], 
                              context: Dict[str, Any]) -> None:
        """Validate email address contact."""
        email = contact.get('value', '').lower()
        
        # Format validation
        if not self._is_valid_email_format(email):
            validation_result['validation_errors'].append('Invalid email format')
            validation_result['validation_status'] = 'invalid'
            return
        
        # Syntax validation
        if not self._is_valid_email_syntax(email):
            validation_result['validation_errors'].append('Email syntax validation failed')
            validation_result['validation_status'] = 'invalid'
            return
        
        # Domain validation
        domain_validation = self._validate_email_domain(email)
        if not domain_validation['valid']:
            validation_result['validation_warnings'].append(domain_validation['warning'])
            validation_result['validation_status'] = 'uncertain'
        
        # MX record check (if enabled)
        if self.dns_check_enabled:
            mx_validation = self._check_email_mx_record(email)
            if not mx_validation['has_mx']:
                validation_result['validation_warnings'].append('No MX record found for domain')
                validation_result['validation_status'] = 'uncertain'
        
        # Disposable email check
        if self._is_disposable_email(email):
            validation_result['validation_warnings'].append('Disposable email address detected')
            validation_result['validation_status'] = 'uncertain'
        
        # Determine final status
        if not validation_result['validation_errors']:
            validation_result['validation_status'] = 'valid'
            validation_result['confidence_adjustment'] = 0.1
        elif validation_result['validation_warnings']:
            validation_result['validation_status'] = 'uncertain'
            validation_result['confidence_adjustment'] = -0.05
        else:
            validation_result['validation_status'] = 'invalid'
            validation_result['confidence_adjustment'] = -0.3
    
    def _validate_website_contact(self, contact: Dict[str, Any], 
                                validation_result: Dict[str, Any], 
                                context: Dict[str, Any]) -> None:
        """Validate website URL contact."""
        url = contact.get('value', '')
        
        # URL format validation
        if not self._is_valid_url_format(url):
            validation_result['validation_errors'].append('Invalid URL format')
            validation_result['validation_status'] = 'invalid'
            return
        
        # HTTP accessibility check
        if self.external_services.get('http_check', False):
            self._check_website_accessibility(url, validation_result)
        
        # Domain validation
        domain_validation = self._validate_website_domain(url)
        if not domain_validation['valid']:
            validation_result['validation_warnings'].append(domain_validation['warning'])
            validation_result['validation_status'] = 'uncertain'
        
        # Determine final status
        if not validation_result['validation_errors']:
            validation_result['validation_status'] = 'valid'
            validation_result['confidence_adjustment'] = 0.05
        elif validation_result['validation_warnings']:
            validation_result['validation_status'] = 'uncertain'
            validation_result['confidence_adjustment'] = -0.05
        else:
            validation_result['validation_status'] = 'invalid'
            validation_result['confidence_adjustment'] = -0.2
    
    def _validate_name_contact(self, contact: Dict[str, Any], 
                             validation_result: Dict[str, Any], 
                             context: Dict[str, Any]) -> None:
        """Validate name contact."""
        name = contact.get('value', '')
        
        # Format validation
        if not self._is_valid_name_format(name):
            validation_result['validation_errors'].append('Invalid name format')
            validation_result['validation_status'] = 'invalid'
            return
        
        # Length validation
        if len(name.strip()) < 2:
            validation_result['validation_errors'].append('Name too short')
            validation_result['validation_status'] = 'invalid'
            return
        
        # Character validation
        if not self._contains_valid_name_characters(name):
            validation_result['validation_warnings'].append('Name contains unusual characters')
            validation_result['validation_status'] = 'uncertain'
        
        # Determine final status
        if not validation_result['validation_errors']:
            validation_result['validation_status'] = 'valid'
            validation_result['confidence_adjustment'] = 0.05
        elif validation_result['validation_warnings']:
            validation_result['validation_status'] = 'uncertain'
            validation_result['confidence_adjustment'] = -0.05
        else:
            validation_result['validation_status'] = 'invalid'
            validation_result['confidence_adjustment'] = -0.2
    
    # Helper validation methods
    def _is_valid_phone_format(self, phone: str) -> bool:
        """Check if phone number has valid format."""
        try:
            parsed = phonenumbers.parse(phone, None)
            return phonenumbers.is_valid_number(parsed)
        except:
            return False
    
    def _detect_phone_country(self, phone: str) -> Optional[str]:
        """Detect phone number country."""
        try:
            parsed = phonenumbers.parse(phone, None)
            region_code = phonenumbers.region_code_for_number(parsed)
            return region_code
        except:
            return None
    
    def _validate_german_phone(self, phone: str, validation_result: Dict[str, Any]) -> None:
        """Specific validation for German phone numbers."""
        try:
            parsed = phonenumbers.parse(phone, 'DE')
            number_type = phonenumbers.number_type(parsed)
            
            # Check number type
            if number_type == PhoneNumberType.UNKNOWN:
                validation_result['validation_warnings'].append('Phone number type unknown')
            elif number_type == PhoneNumberType.FIXED_LINE:
                validation_result['validation_metadata']['type'] = 'fixed_line'
            elif number_type == PhoneNumberType.MOBILE:
                validation_result['validation_metadata']['type'] = 'mobile'
            elif number_type == PhoneNumberType.TOLL_FREE:
                validation_result['validation_metadata']['type'] = 'toll_free'
            
            # Get location info
            location = geocoder.description_for_number(parsed, 'de')
            if location:
                validation_result['validation_metadata']['location'] = location
                
        except Exception as e:
            validation_result['validation_warnings'].append(f'German validation failed: {str(e)}')
    
    def _validate_phone_reality(self, phone: str, validation_result: Dict[str, Any]) -> None:
        """Check if phone number appears to be real."""
        # This would integrate with phone validation services
        # For now, just check basic criteria
        clean_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
        
        # Avoid obviously fake numbers
        fake_patterns = [
            r'000000', r'111111', r'123456',
            r'012345', r'987654', r'555555'
        ]
        
        for pattern in fake_patterns:
            if pattern in clean_phone:
                validation_result['validation_warnings'].append('Phone number appears fake')
                break
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Check if email has valid format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_email_syntax(self, email: str) -> bool:
        """Advanced email syntax validation."""
        # Split email
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        
        # Local part validation
        if len(local) > 64 or len(domain) > 255:
            return False
        
        # Domain validation
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False
        
        # TLD validation
        tld = domain_parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False
        
        return True
    
    def _validate_email_domain(self, email: str) -> Dict[str, Any]:
        """Validate email domain."""
        domain = email.split('@')[1]
        
        # Check domain format
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not re.match(domain_pattern, domain):
            return {'valid': False, 'warning': 'Invalid domain format'}
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'test', r'example', r'dummy', r'fake',
            r'no-reply', r'noreply'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return {'valid': True, 'warning': 'Suspicious domain name'}
        
        return {'valid': True, 'warning': None}
    
    def _check_email_mx_record(self, email: str) -> Dict[str, Any]:
        """Check if domain has MX records."""
        domain = email.split('@')[1]
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return {
                'has_mx': len(mx_records) > 0,
                'mx_records': [str(record.exchange) for record in mx_records]
            }
        except:
            return {'has_mx': False, 'mx_records': []}
    
    def _is_disposable_email(self, email: str) -> bool:
        """Check if email is from a disposable email service."""
        domain = email.split('@')[1].lower()
        
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'yopmail.com', 'throwaway.email'
        ]
        
        return domain in disposable_domains
    
    def _is_valid_url_format(self, url: str) -> bool:
        """Check if URL has valid format."""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(url_pattern, url) is not None
    
    def _check_website_accessibility(self, url: str, validation_result: Dict[str, Any]) -> None:
        """Check if website is accessible."""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                validation_result['validation_metadata']['accessible'] = True
                validation_result['validation_metadata']['status_code'] = response.status_code
            else:
                validation_result['validation_warnings'].append(f'Website returned status: {response.status_code}')
                validation_result['validation_metadata']['accessible'] = False
        except requests.exceptions.RequestException as e:
            validation_result['validation_warnings'].append(f'Website not accessible: {str(e)}')
            validation_result['validation_metadata']['accessible'] = False
    
    def _validate_website_domain(self, url: str) -> Dict[str, Any]:
        """Validate website domain."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Basic domain validation
            if not domain:
                return {'valid': False, 'warning': 'Invalid domain'}
            
            # Check for suspicious domains
            suspicious_patterns = [
                r'localhost', r'127\.0\.0\.1', r'192\.168\.',
                r'test', r'example', r'dummy'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, domain, re.IGNORECASE):
                    return {'valid': False, 'warning': 'Suspicious domain'}
            
            return {'valid': True, 'warning': None}
            
        except Exception as e:
            return {'valid': False, 'warning': f'Domain validation error: {str(e)}'}
    
    def _is_valid_name_format(self, name: str) -> bool:
        """Check if name has valid format."""
        # Remove extra whitespace
        clean_name = ' '.join(name.split())
        
        # Basic format check
        if len(clean_name) < 2:
            return False
        
        # Check for reasonable character usage
        allowed_chars = re.compile(r'^[a-zA-ZäöüßÄÖÜß\s\-\'\.]+$')
        return allowed_chars.match(clean_name) is not None
    
    def _contains_valid_name_characters(self, name: str) -> bool:
        """Check if name contains valid characters."""
        # Count invalid characters
        invalid_chars = re.findall(r'[^a-zA-ZäöüßÄÖÜß\s\-\'\.]', name)
        return len(invalid_chars) == 0 or len(invalid_chars) / len(name) < 0.1
```

### Quality Assessment System
```python
# mfa/contact_discovery/quality_assessment.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)

class ContactQualityAssessment:
    """Comprehensive contact quality assessment system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.quality_weights = config.get('quality_weights', {
            'completeness': 0.3,
            'accuracy': 0.3,
            'confidence': 0.2,
            'freshness': 0.1,
            'relevance': 0.1
        })
        
        self.thresholds = config.get('quality_thresholds', {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        })
    
    def assess_contact_quality(self, contact: Dict[str, Any], 
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Assess quality of a single contact."""
        context = context or {}
        
        # Calculate individual quality dimensions
        completeness = self._assess_completeness(contact, context)
        accuracy = self._assess_accuracy(contact, context)
        confidence = self._assess_confidence(contact, context)
        freshness = self._assess_freshness(contact, context)
        relevance = self._assess_relevance(contact, context)
        
        # Calculate weighted overall score
        overall_score = (
            completeness * self.quality_weights['completeness'] +
            accuracy * self.quality_weights['accuracy'] +
            confidence * self.quality_weights['confidence'] +
            freshness * self.quality_weights['freshness'] +
            relevance * self.quality_weights['relevance']
        )
        
        # Determine quality category
        quality_category = self._determine_quality_category(overall_score)
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            contact, completeness, accuracy, confidence, freshness, relevance
        )
        
        return {
            'overall_score': overall_score,
            'quality_category': quality_category,
            'dimension_scores': {
                'completeness': completeness,
                'accuracy': accuracy,
                'confidence': confidence,
                'freshness': freshness,
                'relevance': relevance
            },
            'quality_thresholds': self.thresholds,
            'improvement_suggestions': suggestions,
            'assessment_metadata': {
                'assessed_at': datetime.utcnow().isoformat(),
                'assessment_version': '1.0',
                'weighting_used': self.quality_weights
            }
        }
    
    def batch_assess_quality(self, contacts: List[Dict[str, Any]], 
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Assess quality for a batch of contacts."""
        context = context or {}
        
        quality_results = []
        for contact in contacts:
            result = self.assess_contact_quality(contact, context)
            quality_results.append(result)
        
        # Calculate batch statistics
        scores = [result['overall_score'] for result in quality_results]
        batch_stats = {
            'total_contacts': len(contacts),
            'average_score': statistics.mean(scores),
            'median_score': statistics.median(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'std_deviation': statistics.stdev(scores) if len(scores) > 1 else 0
        }
        
        # Quality distribution
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        for result in quality_results:
            category = result['quality_category']
            distribution[category] += 1
        
        return {
            'individual_assessments': quality_results,
            'batch_statistics': batch_stats,
            'quality_distribution': distribution,
            'summary': self._generate_quality_summary(batch_stats, distribution)
        }
    
    def _assess_completeness(self, contact: Dict[str, Any], 
                           context: Dict[str, Any]) -> float:
        """Assess data completeness for contact."""
        contact_type = contact.get('type')
        required_fields = self._get_required_fields(contact_type)
        present_fields = []
        
        for field in required_fields:
            if field in contact and contact[field]:
                present_fields.append(field)
        
        # Base completeness score
        base_score = len(present_fields) / len(required_fields) if required_fields else 1.0
        
        # Bonus for additional useful information
        bonus_fields = ['context', 'extraction_method', 'source_field']
        bonus_score = sum(1 for field in bonus_fields if field in contact) / len(bonus_fields)
        
        # Penalize for missing critical information
        penalty = 0.0
        if contact_type in ['phone', 'email'] and not contact.get('value'):
            penalty = 0.5
        
        final_score = min(1.0, base_score + bonus_score * 0.2 - penalty)
        return max(0.0, final_score)
    
    def _assess_accuracy(self, contact: Dict[str, Any], 
                       context: Dict[str, Any]) -> float:
        """Assess data accuracy for contact."""
        validation_status = contact.get('validation_status', 'pending')
        validation_errors = contact.get('validation_errors', [])
        validation_warnings = contact.get('validation_warnings', [])
        
        # Base accuracy from validation
        if validation_status == 'valid':
            base_score = 1.0
        elif validation_status == 'uncertain':
            base_score = 0.6
        elif validation_status == 'invalid':
            base_score = 0.2
        else:  # pending
            base_score = 0.5
        
        # Adjust for validation issues
        error_penalty = len(validation_errors) * 0.3
        warning_penalty = len(validation_warnings) * 0.1
        
        # Confidence adjustment
        confidence = contact.get('confidence', 0.0)
        confidence_bonus = confidence * 0.2
        
        final_score = base_score - error_penalty - warning_penalty + confidence_bonus
        return max(0.0, min(1.0, final_score))
    
    def _assess_confidence(self, contact: Dict[str, Any], 
                         context: Dict[str, Any]) -> float:
        """Assess extraction confidence for contact."""
        confidence = contact.get('confidence', 0.0)
        extraction_method = contact.get('extraction_method', 'unknown')
        
        # Base confidence from extraction confidence
        base_score = confidence
        
        # Method-specific confidence adjustments
        method_multipliers = {
            'api_structured': 1.2,
            'pdf_form': 1.1,
            'ocr': 0.9,
            'manual': 1.0,
            'unknown': 0.7
        }
        
        multiplier = method_multipliers.get(extraction_method, 0.8)
        adjusted_score = base_score * multiplier
        
        # Context quality bonus
        if contact.get('context'):
            adjusted_score += 0.1
        
        return max(0.0, min(1.0, adjusted_score))
    
    def _assess_freshness(self, contact: Dict[str, Any], 
                        context: Dict[str, Any]) -> float:
        """Assess data freshness for contact."""
        extraction_date = contact.get('extraction_date')
        if not extraction_date:
            # No date information, assume medium freshness
            return 0.6
        
        try:
            if isinstance(extraction_date, str):
                extracted_datetime = datetime.fromisoformat(extraction_date.replace('Z', '+00:00'))
            else:
                extracted_datetime = extraction_date
            
            # Calculate age in days
            age_days = (datetime.utcnow() - extracted_datetime.replace(tzinfo=None)).days
            
            # Freshness scoring based on age
            if age_days <= 1:
                return 1.0
            elif age_days <= 7:
                return 0.9
            elif age_days <= 30:
                return 0.8
            elif age_days <= 90:
                return 0.7
            elif age_days <= 365:
                return 0.5
            else:
                return 0.3
                
        except Exception as e:
            logger.warning(f"Freshness assessment failed: {str(e)}")
            return 0.6
    
    def _assess_relevance(self, contact: Dict[str, Any], 
                        context: Dict[str, Any]) -> float:
        """Assess relevance of contact to user's needs."""
        # Context-based relevance
        user_context = context.get('user_search_criteria', {})
        contact_context = contact.get('context', '').lower()
        
        # Keywords relevance
        relevant_keywords = user_context.get('keywords', [])
        if relevant_keywords:
            keyword_matches = sum(1 for keyword in relevant_keywords 
                                if keyword.lower() in contact_context)
            keyword_score = min(1.0, keyword_matches / len(relevant_keywords) * 2)
        else:
            keyword_score = 0.5
        
        # Source relevance
        preferred_sources = user_context.get('preferred_sources', [])
        contact_source = contact.get('extraction_method', '')
        
        if preferred_sources and contact_source in preferred_sources:
            source_score = 1.0
        elif preferred_sources:
            source_score = 0.3
        else:
            source_score = 0.7
        
        # Quality-based relevance
        contact_quality = contact.get('quality_score', 0.5)
        quality_score = contact_quality
        
        # Combine relevance factors
        final_score = (keyword_score * 0.4 + source_score * 0.3 + quality_score * 0.3)
        return max(0.0, min(1.0, final_score))
    
    def _determine_quality_category(self, score: float) -> str:
        """Determine quality category from score."""
        if score >= self.thresholds['excellent']:
            return 'excellent'
        elif score >= self.thresholds['good']:
            return 'good'
        elif score >= self.thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
    
    def _get_required_fields(self, contact_type: str) -> List[str]:
        """Get required fields for contact type."""
        field_requirements = {
            'phone': ['value', 'type'],
            'email': ['value', 'type'],
            'website': ['value', 'type'],
            'name': ['value', 'type']
        }
        return field_requirements.get(contact_type, ['value', 'type'])
    
    def _generate_improvement_suggestions(self, contact: Dict[str, Any], 
                                        completeness: float, accuracy: float,
                                        confidence: float, freshness: float,
                                        relevance: float) -> List[str]:
        """Generate suggestions for improving contact quality."""
        suggestions = []
        
        if completeness < 0.7:
            suggestions.append("Add more complete contact information")
            if not contact.get('context'):
                suggestions.append("Include context information about the contact source")
        
        if accuracy < 0.7:
            suggestions.append("Validate contact information using external services")
            if contact.get('validation_errors'):
                suggestions.append(f"Resolve validation errors: {', '.join(contact['validation_errors'])}")
        
        if confidence < 0.7:
            extraction_method = contact.get('extraction_method', 'unknown')
            if extraction_method == 'ocr':
                suggestions.append("Try alternative extraction methods for better accuracy")
            elif extraction_method == 'manual':
                suggestions.append("Verify manually entered information")
        
        if freshness < 0.7:
            suggestions.append("Contact information may be outdated - consider re-extraction")
        
        if relevance < 0.7:
            suggestions.append("Improve contact relevance to user search criteria")
        
        return suggestions
    
    def _generate_quality_summary(self, batch_stats: Dict[str, Any], 
                                distribution: Dict[str, int]) -> str:
        """Generate human-readable quality summary."""
        total = batch_stats['total_contacts']
        if total == 0:
            return "No contacts to assess"
        
        excellent_pct = (distribution['excellent'] / total) * 100
        good_pct = (distribution['good'] / total) * 100
        avg_score = batch_stats['average_score']
        
        if excellent_pct >= 50:
            quality_level = "excellent"
        elif good_pct >= 70:
            quality_level = "good"
        elif avg_score >= 0.6:
            quality_level = "acceptable"
        else:
            quality_level = "needs improvement"
        
        return (
            f"Contact batch shows {quality_level} quality "
            f"(avg score: {avg_score:.2f}, "
            f"excellent: {excellent_pct:.1f}%, good: {good_pct:.1f}%)"
        )
```

---

## Contact Deduplication System

### Duplicate Detection
```python
# mfa/contact_discovery/deduplication.py
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from difflib import SequenceMatcher
import hashlib
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DuplicateMatch:
    """Represents a duplicate contact match."""
    contact1_id: str
    contact2_id: str
    similarity_score: float
    match_type: str  # 'exact', 'fuzzy', 'similar'
    match_reasons: List[str]
    confidence: float

class ContactDeduplicator:
    """Contact deduplication system."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get('deduplication_thresholds', {
            'exact_match': 1.0,
            'high_similarity': 0.9,
            'medium_similarity': 0.7,
            'low_similarity': 0.5
        })
        
        self.fuzzy_threshold = config.get('fuzzy_threshold', 0.8)
        self.phone_normalization = config.get('phone_normalization', True)
        self.email_normalization = config.get('email_normalization', True)
    
    def find_duplicates(self, contacts: List[Dict[str, Any]]) -> List[DuplicateMatch]:
        """Find duplicate contacts in a list."""
        duplicates = []
        
        # Pre-process contacts for comparison
        processed_contacts = self._preprocess_contacts(contacts)
        
        # Group contacts by exact matches first
        exact_groups = self._group_by_exact_matches(processed_contacts)
        
        # Find fuzzy matches within groups and across groups
        fuzzy_groups = self._find_fuzzy_matches(processed_contacts)
        
        # Combine and validate matches
        all_matches = self._combine_and_validate_matches(exact_groups, fuzzy_groups)
        
        return all_matches
    
    def _preprocess_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess contacts for deduplication."""
        processed = []
        
        for contact in contacts:
            processed_contact = contact.copy()
            
            # Add normalized fields
            if contact.get('type') == 'phone':
                processed_contact['normalized_value'] = self._normalize_phone(contact.get('value', ''))
            elif contact.get('type') == 'email':
                processed_contact['normalized_value'] = self._normalize_email(contact.get('value', ''))
            else:
                processed_contact['normalized_value'] = contact.get('value', '').lower().strip()
            
            # Add similarity keys
            processed_contact['similarity_keys'] = self._generate_similarity_keys(processed_contact)
            
            # Add hash for exact matching
            processed_contact['content_hash'] = self._generate_content_hash(processed_contact)
            
            processed.append(processed_contact)
        
        return processed
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        if not self.phone_normalization:
            return phone
        
        # Remove all non-digit characters except +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Normalize German numbers
        if normalized.startswith('0049'):
            normalized = '+49' + normalized[4:]
        elif normalized.startswith('0') and len(normalized) > 1:
            normalized = '+49' + normalized[1:]
        
        return normalized
    
    def _normalize_email(self, email: str) -> str:
        """Normalize email address for comparison."""
        if not self.email_normalization:
            return email.lower().strip()
        
        email = email.lower().strip()
        
        # Split local and domain parts
        if '@' in email:
            local, domain = email.split('@', 1)
            
            # Handle common email variations
            local = local.replace('.', '')
            
            # Gmail-specific normalization
            if domain == 'gmail.com':
                if '+' in local:
                    local = local.split('+')[0]
            
            return f"{local}@{domain}"
        
        return email
    
    def _generate_similarity_keys(self, contact: Dict[str, Any]) -> List[str]:
        """Generate keys for similarity matching."""
        keys = []
        contact_type = contact.get('type')
        value = contact.get('normalized_value', '')
        
        if contact_type == 'phone':
            # Phone similarity keys
            keys.append(f"phone:{value}")
            
            # Area code based keys
            if value.startswith('+49'):
                area_code = value[:6] if len(value) >= 6 else value
                keys.append(f"phone_area:{area_code}")
        
        elif contact_type == 'email':
            # Email similarity keys
            keys.append(f"email:{value}")
            
            # Domain-based keys
            if '@' in value:
                domain = value.split('@')[1]
                keys.append(f"email_domain:{domain}")
        
        # Always include type-based keys for cross-type matching
        keys.append(f"type:{contact_type}")
        
        return keys
    
    def _generate_content_hash(self, contact: Dict[str, Any]) -> str:
        """Generate hash for exact matching."""
        # Combine key fields for hashing
        content = f"{contact.get('type', '')}:{contact.get('normalized_value', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _group_by_exact_matches(self, contacts: List[Dict[str, Any]]) -> List[Set[str]]:
        """Group contacts by exact matches."""
        groups = []
        processed_hashes = set()
        
        for contact in contacts:
            contact_hash = contact['content_hash']
            
            if contact_hash in processed_hashes:
                continue
            
            # Find all contacts with same hash
            matching_group = {contact['id']}
            for other_contact in contacts:
                if (other_contact['id'] != contact['id'] and 
                    other_contact['content_hash'] == contact_hash):
                    matching_group.add(other_contact['id'])
            
            if len(matching_group) > 1:
                groups.append(matching_group)
                processed_hashes.update(matching_group)
        
        return groups
    
    def _find_fuzzy_matches(self, contacts: List[Dict[str, Any]]) -> List[Set[str]]:
        """Find fuzzy matches between contacts."""
        fuzzy_groups = []
        processed_contacts = set()
        
        # Group by similarity keys for efficient comparison
        key_groups = self._group_by_similarity_keys(contacts)
        
        for key, contact_ids in key_groups.items():
            if len(contact_ids) <= 1:
                continue
            
            # Compare contacts within this key group
            contact_list = [c for c in contacts if c['id'] in contact_ids]
            
            for i, contact1 in enumerate(contact_list):
                if contact1['id'] in processed_contacts:
                    continue
                
                matching_group = {contact1['id']}
                
                for contact2 in contact_list[i+1:]:
                    if contact2['id'] in processed_contacts:
                        continue
                    
                    similarity = self._calculate_similarity(contact1, contact2)
                    
                    if similarity >= self.fuzzy_threshold:
                        matching_group.add(contact2['id'])
                
                if len(matching_group) > 1:
                    fuzzy_groups.append(matching_group)
                    processed_contacts.update(matching_group)
        
        return fuzzy_groups
    
    def _group_by_similarity_keys(self, contacts: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Group contacts by similarity keys."""
        key_groups = {}
        
        for contact in contacts:
            similarity_keys = contact.get('similarity_keys', [])
            
            for key in similarity_keys:
                if key not in key_groups:
                    key_groups[key] = set()
                key_groups[key].add(contact['id'])
        
        return key_groups
    
    def _calculate_similarity(self, contact1: Dict[str, Any], 
                            contact2: Dict[str, Any]) -> float:
        """Calculate similarity between two contacts."""
        type1 = contact1.get('type')
        type2 = contact2.get('type')
        
        # Different types have low similarity
        if type1 != type2:
            return 0.0
        
        value1 = contact1.get('normalized_value', '')
        value2 = contact2.get('normalized_value', '')
        
        if type1 == 'phone':
            return self._calculate_phone_similarity(value1, value2)
        elif type1 == 'email':
            return self._calculate_email_similarity(value1, value2)
        elif type1 == 'name':
            return self._calculate_name_similarity(value1, value2)
        else:
            # Generic similarity
            return SequenceMatcher(None, value1, value2).ratio()
    
    def _calculate_phone_similarity(self, phone1: str, phone2: str) -> float:
        """Calculate similarity between phone numbers."""
        # Exact match
        if phone1 == phone2:
            return 1.0
        
        # Normalize and compare
        norm1 = re.sub(r'[\s\-\(\)\.]', '', phone1)
        norm2 = re.sub(r'[\s\-\(\)\.]', '', phone2)
        
        # Remove country codes for comparison
        if norm1.startswith('+49') and norm2.startswith('+49'):
            norm1 = norm1[3:]
            norm2 = norm2[3:]
        elif norm1.startswith('0049') and norm2.startswith('0049'):
            norm1 = norm1[4:]
            norm2 = norm2[4:]
        
        # Calculate similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _calculate_email_similarity(self, email1: str, email2: str) -> float:
        """Calculate similarity between email addresses."""
        # Exact match
        if email1 == email2:
            return 1.0
        
        # Split into local and domain parts
        local1, domain1 = email1.split('@', 1) if '@' in email1 else (email1, '')
        local2, domain2 = email2.split('@', 1) if '@' in email2 else (email2, '')
        
        # Domain similarity
        domain_similarity = SequenceMatcher(None, domain1, domain2).ratio()
        
        # Local part similarity
        local_similarity = SequenceMatcher(None, local1, local2).ratio()
        
        # Combined similarity (weight domain higher)
        return (domain_similarity * 0.7 + local_similarity * 0.3)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between names."""
        # Exact match
        if name1.lower() == name2.lower():
            return 1.0
        
        # Normalize names
        norm1 = re.sub(r'[^\w\s]', '', name1.lower()).strip()
        norm2 = re.sub(r'[^\w\s]', '', name2.lower()).strip()
        
        # Calculate similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _combine_and_validate_matches(self, exact_groups: List[Set[str]], 
                                    fuzzy_groups: List[Set[str]]) -> List[DuplicateMatch]:
        """Combine and validate duplicate matches."""
        matches = []
        processed_pairs = set()
        
        # Process exact matches
        for group in exact_groups:
            contacts = list(group)
            for i in range(len(contacts)):
                for j in range(i + 1, len(contacts)):
                    contact1_id = contacts[i]
                    contact2_id = contacts[j]
                    pair_key = tuple(sorted([contact1_id, contact2_id]))
                    
                    if pair_key in processed_pairs:
                        continue
                    
                    matches.append(DuplicateMatch(
                        contact1_id=contact1_id,
                        contact2_id=contact2_id,
                        similarity_score=1.0,
                        match_type='exact',
                        match_reasons=['Identical normalized value'],
                        confidence=0.95
                    ))
                    processed_pairs.add(pair_key)
        
        # Process fuzzy matches
        for group in fuzzy_groups:
            contacts = list(group)
            for i in range(len(contacts)):
                for j in range(i + 1, len(contacts)):
                    contact1_id = contacts[i]
                    contact2_id = contacts[j]
                    pair_key = tuple(sorted([contact1_id, contact2_id]))
                    
                    if pair_key in processed_pairs:
                        continue
                    
                    # Calculate actual similarity
                    similarity = self._calculate_fuzzy_similarity(contact1_id, contact2_id)
                    
                    if similarity >= self.fuzzy_threshold:
                        match_type = 'high_similarity' if similarity >= 0.9 else 'medium_similarity'
                        
                        matches.append(DuplicateMatch(
                            contact1_id=contact1_id,
                            contact2_id=contact2_id,
                            similarity_score=similarity,
                            match_type=match_type,
                            match_reasons=['High similarity score'],
                            confidence=similarity * 0.9
                        ))
                        processed_pairs.add(pair_key)
        
        return matches
    
    def _calculate_fuzzy_similarity(self, contact1_id: str, contact2_id: str) -> float:
        """Calculate detailed fuzzy similarity (placeholder implementation)."""
        # This would compare the actual contact data
        # For now, return a placeholder similarity
        return 0.85
```

### Duplicate Resolution
```python
# mfa/contact_discovery/duplicate_resolution.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ResolutionStrategy(Enum):
    """Strategies for resolving duplicates."""
    KEEP_BEST = "keep_best"
    MERGE_CONTACTS = "merge_contacts"
    MANUAL_REVIEW = "manual_review"
    KEEP_NEWEST = "keep_newest"
    KEEP_OLDEST = "keep_oldest"

@dataclass
class ResolutionResult:
    """Result of duplicate resolution."""
    strategy: ResolutionStrategy
    resolved_contact: Optional[Dict[str, Any]]
    merged_data: Optional[Dict[str, Any]]
    resolution_confidence: float
    conflicts: List[str]
    manual_review_required: bool

class DuplicateResolver:
    """System for resolving duplicate contacts."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_strategy = config.get('default_strategy', ResolutionStrategy.KEEP_BEST)
        self.quality_weights = config.get('quality_weights', {
            'confidence': 0.4,
            'completeness': 0.3,
            'freshness': 0.2,
            'validation_status': 0.1
        })
    
    def resolve_duplicates(self, contacts: List[Dict[str, Any]], 
                          duplicate_matches: List) -> List[ResolutionResult]:
        """Resolve duplicate contacts using specified strategies."""
        results = []
        
        # Group contacts by duplicate clusters
        clusters = self._cluster_duplicates(contacts, duplicate_matches)
        
        for cluster in clusters:
            resolution_result = self._resolve_cluster(cluster)
            results.append(resolution_result)
        
        return results
    
    def _cluster_duplicates(self, contacts: List[Dict[str, Any]], 
                          duplicate_matches: List) -> List[List[Dict[str, Any]]]:
        """Cluster contacts into duplicate groups."""
        # Create adjacency list for duplicate relationships
        adjacency = {contact['id']: set() for contact in contacts}
        
        for match in duplicate_matches:
            adjacency[match.contact1_id].add(match.contact2_id)
            adjacency[match.contact2_id].add(match.contact1_id)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        
        for contact in contacts:
            if contact['id'] in visited:
                continue
            
            # BFS to find cluster
            cluster = []
            queue = [contact['id']]
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                current_contact = next(c for c in contacts if c['id'] == current_id)
                cluster.append(current_contact)
                
                # Add connected contacts to queue
                for neighbor_id in adjacency[current_id]:
                    if neighbor_id not in visited:
                        queue.append(neighbor_id)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def _resolve_cluster(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Resolve a cluster of duplicate contacts."""
        if len(cluster) == 1:
            return ResolutionResult(
                strategy=ResolutionStrategy.KEEP_BEST,
                resolved_contact=cluster[0],
                merged_data=None,
                resolution_confidence=1.0,
                conflicts=[],
                manual_review_required=False
            )
        
        # Apply resolution strategy
        strategy = self.config.get('strategy', self.default_strategy)
        
        if strategy == ResolutionStrategy.KEEP_BEST:
            return self._keep_best_contact(cluster)
        elif strategy == ResolutionStrategy.MERGE_CONTACTS:
            return self._merge_contacts(cluster)
        elif strategy == ResolutionStrategy.KEEP_NEWEST:
            return self._keep_newest_contact(cluster)
        elif strategy == ResolutionStrategy.KEEP_OLDEST:
            return self._keep_oldest_contact(cluster)
        elif strategy == ResolutionStrategy.MANUAL_REVIEW:
            return self._mark_for_manual_review(cluster)
        else:
            # Default to keep best
            return self._keep_best_contact(cluster)
    
    def _keep_best_contact(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Keep the best contact from the cluster."""
        best_contact = None
        best_score = -1
        
        for contact in cluster:
            score = self._calculate_contact_score(contact)
            if score > best_score:
                best_score = score
                best_contact = contact
        
        conflicts = self._identify_conflicts(cluster)
        
        return ResolutionResult(
            strategy=ResolutionStrategy.KEEP_BEST,
            resolved_contact=best_contact,
            merged_data=None,
            resolution_confidence=min(1.0, best_score),
            conflicts=conflicts,
            manual_review_required=len(conflicts) > 0 and best_score < 0.8
        )
    
    def _merge_contacts(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Merge contacts into a single comprehensive contact."""
        merged = cluster[0].copy()  # Start with first contact
        conflicts = []
        
        # Merge fields from all contacts
        for contact in cluster[1:]:
            for key, value in contact.items():
                if key in merged and merged[key] != value:
                    conflicts.append(f"Conflict in {key}: '{merged[key]}' vs '{value}'")
                    
                    # Keep the better value
                    if self._should_keep_new_value(key, merged[key], value):
                        merged[key] = value
        
        # Update metadata
        merged['merged_from'] = [c['id'] for c in cluster]
        merged['merged_at'] = datetime.utcnow().isoformat()
        
        resolution_confidence = self._calculate_merge_confidence(cluster, conflicts)
        
        return ResolutionResult(
            strategy=ResolutionStrategy.MERGE_CONTACTS,
            resolved_contact=merged,
            merged_data=merged,
            resolution_confidence=resolution_confidence,
            conflicts=conflicts,
            manual_review_required=len(conflicts) > 2
        )
    
    def _keep_newest_contact(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Keep the newest contact from the cluster."""
        newest_contact = None
        newest_date = None
        
        for contact in cluster:
            extraction_date = contact.get('extraction_date')
            if extraction_date:
                try:
                    if isinstance(extraction_date, str):
                        contact_date = datetime.fromisoformat(extraction_date.replace('Z', '+00:00'))
                    else:
                        contact_date = extraction_date
                    
                    if newest_date is None or contact_date > newest_date:
                        newest_date = contact_date
                        newest_contact = contact
                except:
                    continue
        
        # If no date available, fall back to keep best
        if newest_contact is None:
            return self._keep_best_contact(cluster)
        
        conflicts = self._identify_conflicts(cluster)
        
        return ResolutionResult(
            strategy=ResolutionStrategy.KEEP_NEWEST,
            resolved_contact=newest_contact,
            merged_data=None,
            resolution_confidence=0.8,
            conflicts=conflicts,
            manual_review_required=False
        )
    
    def _keep_oldest_contact(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Keep the oldest contact from the cluster."""
        oldest_contact = None
        oldest_date = None
        
        for contact in cluster:
            extraction_date = contact.get('extraction_date')
            if extraction_date:
                try:
                    if isinstance(extraction_date, str):
                        contact_date = datetime.fromisoformat(extraction_date.replace('Z', '+00:00'))
                    else:
                        contact_date = extraction_date
                    
                    if oldest_date is None or contact_date < oldest_date:
                        oldest_date = contact_date
                        oldest_contact = contact
                except:
                    continue
        
        # If no date available, fall back to keep best
        if oldest_contact is None:
            return self._keep_best_contact(cluster)
        
        conflicts = self._identify_conflicts(cluster)
        
        return ResolutionResult(
            strategy=ResolutionStrategy.KEEP_OLDEST,
            resolved_contact=oldest_contact,
            merged_data=None,
            resolution_confidence=0.8,
            conflicts=conflicts,
            manual_review_required=False
        )
    
    def _mark_for_manual_review(self, cluster: List[Dict[str, Any]]) -> ResolutionResult:
        """Mark cluster for manual review."""
        conflicts = self._identify_conflicts(cluster)
        
        return ResolutionResult(
            strategy=ResolutionStrategy.MANUAL_REVIEW,
            resolved_contact=None,
            merged_data=None,
            resolution_confidence=0.0,
            conflicts=conflicts,
            manual_review_required=True
        )
    
    def _calculate_contact_score(self, contact: Dict[str, Any]) -> float:
        """Calculate overall score for a contact."""
        score = 0.0
        
        # Confidence score
        confidence = contact.get('confidence', 0.0)
        score += confidence * self.quality_weights['confidence']
        
        # Completeness score
        completeness = self._assess_contact_completeness(contact)
        score += completeness * self.quality_weights['completeness']
        
        # Freshness score
        freshness = self._assess_contact_freshness(contact)
        score += freshness * self.quality_weights['freshness']
        
        # Validation status score
        validation_status = contact.get('validation_status', 'pending')
        if validation_status == 'valid':
            score += 1.0 * self.quality_weights['validation_status']
        elif validation_status == 'uncertain':
            score += 0.5 * self.quality_weights['validation_status']
        else:
            score += 0.0 * self.quality_weights['validation_status']
        
        return score
    
    def _assess_contact_completeness(self, contact: Dict[str, Any]) -> float:
        """Assess completeness of contact."""
        required_fields = ['type', 'value']
        present_fields = sum(1 for field in required_fields if contact.get(field))
        return present_fields / len(required_fields)
    
    def _assess_contact_freshness(self, contact: Dict[str, Any]) -> float:
        """Assess freshness of contact."""
        extraction_date = contact.get('extraction_date')
        if not extraction_date:
            return 0.5
        
        try:
            if isinstance(extraction_date, str):
                contact_date = datetime.fromisoformat(extraction_date.replace('Z', '+00:00'))
            else:
                contact_date = extraction_date
            
            age_days = (datetime.utcnow() - contact_date.replace(tzinfo=None)).days
            
            if age_days <= 1:
                return 1.0
            elif age_days <= 7:
                return 0.9
            elif age_days <= 30:
                return 0.8
            else:
                return 0.5
                
        except:
            return 0.5
    
    def _identify_conflicts(self, cluster: List[Dict[str, Any]]) -> List[str]:
        """Identify conflicts in a cluster of contacts."""
        conflicts = []
        
        # Check for value conflicts
        value_conflicts = self._check_value_conflicts(cluster)
        conflicts.extend(value_conflicts)
        
        # Check for type conflicts
        type_conflicts = self._check_type_conflicts(cluster)
        conflicts.extend(type_conflicts)
        
        return conflicts
    
    def _check_value_conflicts(self, cluster: List[Dict[str, Any]]) -> List[str]:
        """Check for value conflicts in cluster."""
        conflicts = []
        values = [contact.get('value') for contact in cluster]
        unique_values = set(values)
        
        if len(unique_values) > 1:
            conflicts.append(f"Conflicting values: {', '.join(str(v) for v in unique_values)}")
        
        return conflicts
    
    def _check_type_conflicts(self, cluster: List[Dict[str, Any]]) -> List[str]:
        """Check for type conflicts in cluster."""
        conflicts = []
        types = [contact.get('type') for contact in cluster]
        unique_types = set(types)
        
        if len(unique_types) > 1:
            conflicts.append(f"Conflicting types: {', '.join(unique_types)}")
        
        return conflicts
    
    def _should_keep_new_value(self, field: str, old_value: Any, new_value: Any) -> bool:
        """Determine if new value should replace old value."""
        # Field-specific rules
        if field == 'confidence':
            return new_value > old_value
        elif field == 'extraction_date':
            try:
                old_date = datetime.fromisoformat(str(old_value).replace('Z', '+00:00'))
                new_date = datetime.fromisoformat(str(new_value).replace('Z', '+00:00'))
                return new_date > old_date
            except:
                return False
        elif field == 'validation_status':
            # Prefer valid over invalid
            status_priority = {'valid': 3, 'uncertain': 2, 'invalid': 1, 'pending': 0}
            return status_priority.get(new_value, 0) > status_priority.get(old_value, 0)
        
        # Default: keep the value with higher confidence
        return False
    
    def _calculate_merge_confidence(self, cluster: List[Dict[str, Any]], 
                                  conflicts: List[str]) -> float:
        """Calculate confidence in merge result."""
        base_confidence = 1.0
        
        # Reduce confidence for each conflict
        conflict_penalty = len(conflicts) * 0.1
        
        # Reduce confidence if high-scoring contact not used
        best_contact = max(cluster, key=self._calculate_contact_score)
        if best_contact.get('id') != cluster[0].get('id'):
            conflict_penalty += 0.2
        
        return max(0.0, base_confidence - conflict_penalty)
```

---

## Related Documentation

- [Database Schema](database-schema.md) - Database structures for contact storage
- [Data Models](data-models.md) - Contact data models and relationships
- [System Overview](../architecture/system-overview.md) - Overall system architecture
- [API Documentation](../developer-guide/api/integration-guide.md) - API endpoints for contact discovery
- [Security Guide](../operations/security.md) - Security considerations for contact data

---

**Contact Discovery Support**: For contact discovery issues or questions, contact the discovery team or create an issue with the `contact-discovery` label.