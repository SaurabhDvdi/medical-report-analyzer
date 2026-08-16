from typing import Optional, Dict, Any, List
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from logging_config import get_logger

logger = get_logger(__name__)


class Seq2SeqSummarizer:
    """Clean shared seq2seq summarizer wrapper compatible with Transformers v5+."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def __call__(self, text: str, max_length: int = 150, min_length: int = 30, do_sample: bool = False) -> List[Dict[str, str]]:
        prefix = "summarize: " if "t5" in self.model_name.lower() else ""
        input_text = prefix + text
        inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=1024)
        
        # Ensure min_length is not greater than max_length
        actual_min_len = min(min_length, max_length - 5) if max_length > 10 else 5
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            min_length=actual_min_len,
            do_sample=do_sample
        )
        summary_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        return [{"summary_text": summary_text}]


class NLPService:
    def __init__(self):
        try:
            logger.info("Loading BART summarization model (facebook/bart-large-cnn)...")
            self.summarizer = Seq2SeqSummarizer("facebook/bart-large-cnn")
        except Exception as e:
            logger.error(f"Error loading BART model: {str(e)}")
            try:
                logger.info("Fallback: Loading T5 summarization model (t5-small)...")
                self.summarizer = Seq2SeqSummarizer("t5-small")
            except Exception as e2:
                logger.error(f"Error loading T5 model: {str(e2)}")
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
                text_truncated = text[:1024]
                summary = self.summarizer(
                    text_truncated,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                return summary[0]['summary_text']
            except Exception as e:
                logger.error(f"Transformer summarization failed: {str(e)}")

        # Level 2: Extract first 3 sentences (fallback if model fails)
        try:
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            if sentences:
                return ".".join(sentences[:3]) + "."
        except Exception as e:
            logger.error(f"Extractive summary failed: {str(e)}")

        # Level 3: Return first 300 chars if all else fails
        return text[:300]
