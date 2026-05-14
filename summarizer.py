import os
import time
from utils import setup_logger

logger = setup_logger(__name__)

try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class DescriptionSummarizer:
    """Summarizes product descriptions using LLM (Gemini API) with retry logic."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.enabled = False
        
        if self.api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                # Using gemini-1.5-flash for fast and cost-effective text tasks
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                logger.info("DescriptionSummarizer initialized successfully with Gemini API.")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini API: {e}. Summarization will be disabled.")
        else:
            if not GENAI_AVAILABLE:
                logger.warning("google-generativeai is not installed. Summarization is disabled.")
            elif not self.api_key:
                logger.warning("GEMINI_API_KEY not found in environment. Summarization is disabled.")

    def summarize(self, description):
        """Returns summarized text if enabled, else returns None. Includes retry logic."""
        if not self.enabled or not description or description == "N/A":
            return None
            
        # If description is already very short, no need to summarize
        if len(description) < 200:
            return None
            
        prompt = (
            "You are a professional medical product description summarizer. "
            "Please provide a very short, clean, and professional summary (1-3 sentences) of the following product description. "
            "Do not include any introductory or concluding remarks, just the summary.\n\n"
            f"Description:\n{description}"
        )
        
        max_retries = 3
        base_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response.text:
                    return response.text.strip()
            except (ResourceExhausted, DeadlineExceeded) as e:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Gemini API rate limit or timeout (Attempt {attempt+1}/{max_retries}). Waiting {delay}s... ({e})")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Summarization failed unexpectedly: {e}")
                break  # Don't retry on other unknown errors
                
        logger.error("Summarization failed after maximum retries. Returning original only.")
        return None
