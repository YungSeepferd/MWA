"""
OCR-based contact extraction for images.

This module provides functionality to extract contact information
from images using Tesseract OCR.
"""

import logging
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from urllib.parse import urlparse

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .extractor import ContactExtractor
from .models import Contact, ContactMethod, ConfidenceLevel, DiscoveryContext
from ..config.settings import Settings

@dataclass
class ExtractedContact:
    """
    Represents a contact extracted from an image via OCR.
    
    Attributes:
        source: Source image/file path or URL
        contact: The extracted contact information
        context: Additional context for extraction
        raw_data: Raw OCR data and processing information
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

class OCRExtractor(ContactExtractor):
    """
    Extracts contact information from images using OCR.
    
    Supports various image formats and preprocessing techniques
    to improve OCR accuracy.
    """
    
    def __init__(
        self,
        config: Settings,
        languages: Optional[List[str]] = None,
        confidence_threshold: float = 0.7,
        preprocess: bool = True,
        enhance_contrast: bool = True,
        denoise: bool = True
    ):
        """
        Initialize OCR extractor.
        
        Args:
            config: Settings object
            languages: List of language codes for OCR (e.g., ['deu', 'eng'])
            confidence_threshold: Minimum confidence score for extracted contacts
            preprocess: Whether to apply image preprocessing
            enhance_contrast: Whether to enhance image contrast
            denoise: Whether to apply denoising
        """
        super().__init__(config)
        self.languages = languages or ['deu', 'eng']
        self.confidence_threshold = confidence_threshold
        self.preprocess = preprocess
        self.enhance_contrast = enhance_contrast
        self.denoise = denoise
        
        # Try to import pytesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
            # Configure Tesseract path if needed
            # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        except ImportError:
            logger.error("pytesseract not installed. OCR extraction will be disabled.")
            self.pytesseract = None
    
    def can_process(self, source: Union[str, Path, bytes]) -> bool:
        """
        Check if the source can be processed by this extractor.
        
        Args:
            source: Image URL, file path, or image data
            
        Returns:
            True if the source is an image that can be processed
        """
        if isinstance(source, str):
            # Check if it's a URL or file path
            if source.startswith(('http://', 'https://')):
                # Check file extension
                parsed = urlparse(source)
                ext = Path(parsed.path).suffix.lower()
                return ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']
            else:
                # Check if file exists and is an image
                path = Path(source)
                return path.exists() and path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']
        elif isinstance(source, (Path, bytes)):
            return True
        return False
    
    def extract_contacts(
        self,
        source: Union[str, Path, bytes],
        context: Optional[Dict] = None
    ) -> List[ExtractedContact]:
        """
        Extract contacts from an image using OCR.
        
        Args:
            source: Image URL, file path, or image data
            context: Additional context for extraction
            
        Returns:
            List of extracted contacts with confidence scores
        """
        if not self.pytesseract:
            logger.warning("OCR extraction disabled - pytesseract not available")
            return []
        
        try:
            # Load image
            image = self._load_image(source)
            if image is None:
                return []
            
            # Preprocess image if enabled
            if self.preprocess:
                image = self._preprocess_image(image)
            
            # Extract text using OCR
            text = self._extract_text(image)
            if not text:
                logger.debug("No text extracted from image")
                return []
            
            logger.debug(f"Extracted text from image: {text[:200]}...")
            
            # Extract contacts from text
            contacts = self._extract_contacts_from_text(text, source, context)
            
            # Score contacts based on image quality and extraction confidence
            scored_contacts = self._score_contacts(contacts, image, text)
            
            # Filter by confidence threshold
            filtered_contacts = [
                contact for contact in scored_contacts
                if self._convert_confidence_level(contact.contact.confidence) >= self.confidence_threshold
            ]
            
            logger.info(f"Extracted {len(filtered_contacts)} contacts from image")
            return filtered_contacts
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def _load_image(self, source: Union[str, Path, bytes]) -> Optional[Image.Image]:
        """Load image from various sources."""
        try:
            if isinstance(source, str):
                if source.startswith(('http://', 'https://')):
                    # Download image from URL
                    import requests
                    response = requests.get(source, timeout=10)
                    response.raise_for_status()
                    return Image.open(BytesIO(response.content))
                else:
                    # Load from file path
                    return Image.open(source)
            elif isinstance(source, Path):
                return Image.open(source)
            elif isinstance(source, bytes):
                from io import BytesIO
                return Image.open(BytesIO(source))
            else:
                logger.error(f"Unsupported source type: {type(source)}")
                return None
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply preprocessing to improve OCR accuracy."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance contrast
            if self.enhance_contrast:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)  # Increase contrast by 50%
            
            # Apply sharpening
            image = image.filter(ImageFilter.SHARPEN)
            
            # Convert to OpenCV format for advanced processing
            cv_image = np.array(image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            # Denoise if enabled
            if self.denoise:
                cv_image = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)
            
            # Convert back to PIL
            image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            # Configure OCR parameters
            config_parts = []
            if self.languages:
                config_parts.append(f'-l {"+".join(self.languages)}')
            config_parts.append('--psm 3')  # Fully automatic page segmentation
            
            config = ' '.join(config_parts)
            
            # Extract text
            text = self.pytesseract.image_to_string(image, config=config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR text extraction failed: {e}")
            return ""
    
    def _extract_contacts_from_text(
        self,
        text: str,
        source: Union[str, Path, bytes],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from OCR text using pattern matching."""
        contacts = []
        
        # Extract emails
        emails = self._extract_emails(text)
        for email, confidence in emails:
            contact = Contact(
                method=ContactMethod.EMAIL,
                value=email,
                confidence=confidence,
                source_url=str(source),
                metadata={"ocr_extracted": True}
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
                metadata={"ocr_extracted": True}
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
                metadata={"ocr_extracted": True}
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, form_url)}
            )
            contacts.append(extracted)
        
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
        image: Image.Image,
        text: str
    ) -> List[ExtractedContact]:
        """Score contacts based on image quality and extraction confidence."""
        # Calculate image quality metrics
        image_quality = self._calculate_image_quality(image)
        text_quality = self._calculate_text_quality(text)
        
        # Adjust contact scores based on quality metrics
        scored_contacts = []
        for contact in contacts:
            # Base confidence from pattern matching
            base_confidence = self._convert_confidence_level(contact.contact.confidence)
            
            # Adjust based on image quality
            quality_adjustment = (image_quality + text_quality) / 2
            
            # Calculate final confidence
            final_confidence = min(1.0, base_confidence * quality_adjustment)
            
            # Update contact confidence
            contact.contact.confidence = self._convert_to_confidence_level(final_confidence)
            scored_contacts.append(contact)
        
        return scored_contacts
    
    def _calculate_image_quality(self, image: Image.Image) -> float:
        """Calculate image quality score (0-1)."""
        try:
            # Convert to grayscale for analysis
            gray = np.array(image.convert('L'))
            
            # Calculate sharpness using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            
            # Normalize sharpness (typical range: 0-1000)
            sharpness_score = min(1.0, sharpness / 1000.0)
            
            # Calculate contrast
            contrast = gray.std() / 255.0
            
            # Combine metrics
            quality = (sharpness_score + contrast) / 2
            
            return max(0.1, min(1.0, quality))  # Ensure minimum quality score
            
        except Exception as e:
            logger.warning(f"Image quality calculation failed: {e}")
            return 0.5  # Default medium quality
    
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
    # Initialize OCR extractor
    extractor = OCRExtractor(
        languages=['deu', 'eng'],
        confidence_threshold=0.6,
        preprocess=True
    )
    
    # Test with a sample image
    test_image = "path/to/contact_card.png"
    
    if extractor.can_process(test_image):
        contacts = extractor.extract_contacts(test_image)
        
        for contact in contacts:
            print(f"Found {contact.contact.method}: {contact.contact.value} "
                  f"(confidence: {contact.contact.confidence.name})")
    else:
        print("Cannot process the provided image")