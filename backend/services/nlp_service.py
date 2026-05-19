from transformers import pipeline
from typing import Optional

class NLPService:
    def __init__(self):
        # Initialize summarization model
        try:
            # Use a smaller model for local processing
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # CPU
            )
        except Exception as e:
            print(f"Error loading BART model: {str(e)}")
            try:
                # Fallback to T5
                self.summarizer = pipeline(
                    "summarization",
                    model="t5-small",
                    device=-1
                )
            except Exception as e2:
                print(f"Error loading T5 model: {str(e2)}")
                self.summarizer = None
    
    def generate_summary(self, text, max_length: int = 150, min_length: int = 50) -> str:
        """Generate AI summary of medical report text
        
        Args:
            text: Either str or List[str] — if list, joins with spaces first
        """
        # Accept List[str] or str
        if isinstance(text, list):
            text = " ".join(str(item) for item in text)
        
        text = str(text).strip()
        if not text:
            return ""
        
        # Try transformer pipeline first
        if self.summarizer is not None:
            try:
                # Truncate text if too long (models have token limits)
                max_input_length = 1024
                if len(text) > max_input_length:
                    text_truncated = text[:max_input_length]
                else:
                    text_truncated = text
                
                summary = self.summarizer(
                    text_truncated,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                return summary[0]['summary_text']
            except Exception as e:
                print(f"Transformer summarization failed: {str(e)}")
        
        # Fallback: extractive summary — first 3 sentences > 20 chars
        try:
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            if sentences:
                return ".".join(sentences[:3]) + "."
        except Exception as e:
            print(f"Extractive summary failed: {str(e)}")
        
        # Last resort: return first 300 characters
        return text[:300]

