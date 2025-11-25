import google.generativeai as genai
from onepassword_config import get_config_value
from textual import log

class GeminiSummarizer:
    """A class to handle message summarization using Google's Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini API client"""

        self.api_key = get_config_value("GEMINI_API_KEY")
        if not self.api_key:
            log.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
            return
            
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
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
    
    async def summarize_multiple_messages(self, messages: list) -> str:
        """
        Summarize multiple messages using Gemini API
        
        Args:
            messages: List of message dictionaries to summarize
            
        Returns:
            Summary string or error message
        """
        if not self.is_available():
            return "Gemini API not available. Please set GEMINI_API_KEY environment variable."
        
        if not messages:
            return "No messages to summarize."
        
        try:
            # Build a structured representation of all messages
            messages_text = []
            for i, msg in enumerate(messages, 1):
                subject = msg.get('subject', 'No subject')
                body = msg.get('body', 'No content')
                author_info = msg.get('author', {})
                author_name = f"{author_info.get('firstName', '')} {author_info.get('lastName', '')}".strip() or "Unknown author"
                source = msg.get('source', 'unknown')
                age = msg.get('age', 'unknown time')
                
                messages_text.append(f"""
Message {i}:
- Source: {source}
- Posted: {age}
- Author: {author_name}
- Subject: {subject}
- Content: {body[:500]}{"..." if len(body) > 500 else ""}
""")
            
            combined_messages = "\n".join(messages_text)
            
            # Create prompt for summarization
            prompt = f"""
Please analyze and summarize the following {len(messages)} message(s) from a community forum/social media feed:

{combined_messages}

Please provide:
1. **Executive Summary**: A brief overview of the main themes and topics across all messages (2-3 sentences)
2. **Key Topics**: List the 3-5 most important topics or issues discussed
3. **Notable Concerns**: Any urgent issues, questions, or concerns that stand out
4. **Suggested Next Steps**: 3-5 actionable recommendations for addressing the topics discussed

Format your response in clear sections with proper headings. Keep it concise but comprehensive.
"""
            
            # Generate summary
            response = await self.model.generate_content_async(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Failed to generate summary. Please try again."
                
        except Exception as e:
            log.error(f"Error generating multi-message summary: {e}")
            return f"Error generating summary: {str(e)}"