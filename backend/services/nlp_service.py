from transformers import pipeline
from typing import Optional
from logging_config import get_logger

logger = get_logger(__name__)

class NLPService:
    def __init__(self):
        try:
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1
            )
        except Exception as e:
            print(f"Error loading BART model: {str(e)}")
            try:
                # Fallback to T5 if BART unavailable
                self.summarizer = pipeline(
                    "summarization",
                    model="t5-small",
                    device=-1
                )
            except Exception as e2:
                print(f"Error loading T5 model: {str(e2)}")
                self.summarizer = None
    
    def generate_summary(self, text, max_length: int = 150, min_length: int = 50) -> str:
        # Accepts str or List[str] (joins list with spaces)
        if isinstance(text, list):
            text = " ".join(str(item) for item in text)
        
        text = str(text).strip()
        if not text:
            return ""
        
        # Level 1: Transformer model (BART/T5)
        if self.summarizer is not None:
            try:
                # Truncate to 1024 chars (model token limit)
                text_truncated = text[:1024]
                summary = self.summarizer(
                    text_truncated,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                return summary[0]['summary_text']
            except Exception as e:
                print(f"Transformer summarization failed: {str(e)}")
        
        # Level 2: Extract first 3 sentences (fallback if model fails)
        try:
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            if sentences:
                return ".".join(sentences[:3]) + "."
        except Exception as e:
            print(f"Extractive summary failed: {str(e)}")
        
        # Level 3: Return first 300 chars if all else fails
        return text[:300]

