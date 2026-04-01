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
    
    def generate_summary(self, text: str, max_length: int = 150, min_length: int = 50) -> str:
        """Generate AI summary of medical report text"""
        if not text or len(text.strip()) < 50:
            return "Text too short for summarization"
        
        if self.summarizer is None:
            # Fallback: return first 200 characters
            return text[:200] + "..." if len(text) > 200 else text
        
        try:
            # Truncate text if too long (models have token limits)
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
            
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            
            return summary[0]['summary_text']
        except Exception as e:
            print(f"Summarization error: {str(e)}")
            # Fallback: return first 200 characters
            return text[:200] + "..." if len(text) > 200 else text

