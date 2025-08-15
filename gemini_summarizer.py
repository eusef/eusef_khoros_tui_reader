import os
import google.generativeai as genai
from dotenv import load_dotenv
from textual import log

# Load environment variables
load_dotenv()

class GeminiSummarizer:
    """A class to handle message summarization using Google's Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini API client"""

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            log.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
            return
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            log.info("Gemini API client initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Gemini API: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if the Gemini API is available"""
        return self.api_key is not None and self.model is not None
    
    async def summarize_message(self, message_data: dict) -> str:
        """
        Summarize a message using Gemini API
        
        Args:
            message_data: Dictionary containing message information
            
        Returns:
            Summary string or error message
        """
        if not self.is_available():
            return "Gemini API not available. Please set GEMINI_API_KEY environment variable."
        
        try:
            # Extract relevant message content
            subject = message_data.get('subject', 'No subject')
            body = message_data.get('body', 'No content')
            author_info = message_data.get('author', {})
            author_name = f"{author_info.get('firstName', '')} {author_info.get('lastName', '')}".strip() or "Unknown author"
            
            # Create prompt for summarization
            prompt = f"""
            Please provide a concise summary of the following message from a community forum:
            
            Subject: {subject}
            Author: {author_name}
            Content: {body}
            
            Please summarize the key points in 2-3 sentences, focusing on:
            - The main topic or question
            - Any specific requests or issues mentioned
            - The overall tone and context
            
            Keep the summary clear and professional.
            """
            
            # Generate summary
            response = await self.model.generate_content_async(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Failed to generate summary. Please try again."
                
        except Exception as e:
            log.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def get_status_message(self) -> str:
        """Get a status message about the Gemini API availability"""
        if self.is_available():
            return "Gemini API: Available"
        else:
            return "Gemini API: Not available (set GEMINI_API_KEY)"
    
    async def test_connection(self) -> str:
        """Test the Gemini API connection with a simple prompt"""
        if not self.is_available():
            return "Gemini API not available"
        
        try:
            response = await self.model.generate_content_async("Hello! Please respond with 'Connection successful' if you can see this message.")
            if response and response.text:
                return f"Test successful: {response.text.strip()}"
            else:
                return "Test failed: No response received"
        except Exception as e:
            return f"Test failed: {str(e)}"
