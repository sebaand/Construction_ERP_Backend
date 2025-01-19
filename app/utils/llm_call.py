import anthropic
import os
from botocore.exceptions import ClientError
import logging
from typing import Optional, Union
import base64
import json
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# # Load and encode the PDF
# pdf_url = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
# pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")


def save_to_json(content: str, response_type: str = "form_analysis") -> None:
    """
    Save API response content to a JSON file with timestamp.
    
    Args:
        content (str): The content to save
        response_type (str): Type of response for filename
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create filename
    filename = log_dir / f"{response_type}_{timestamp}.json"
    
    # Prepare data structure
    data = {
        "timestamp": timestamp,
        "type": response_type,
        "content": content
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved response to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON: {str(e)}")

def read_and_encode_file(file_path: str) -> str:
    """
    Read a PDF file and encode it to base64.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Base64 encoded PDF content
    """
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            return base64.b64encode(file_content).decode('utf-8')
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        raise


def llm_call(content: str, file_path: str, system_prompt: str = None) -> Union[str, bool]:
    """
    Make a call to the Anthropic Claude API with error handling and logging.
    
    Args:
        content (str): The prompt content to send to the model
        pdf_path (str): Path to the file to analyze
        
    Returns:
        Union[str, bool]: The model's response text, or False if an error occurred
    """
    try:
        # Encode the PDF file
        data = read_and_encode_file(file_path)
        
        message_params = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            # "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                # "media_type": "image/jpeg",
                                "data": data,            
                            }
                        },
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            ],
        }

        # Add system prompt if provided
        if system_prompt:
            message_params["system"] = system_prompt
            
        message = client.messages.create(**message_params)
        
        if hasattr(message, 'content'):
            logger.debug(f"Successful API call with content length: {len(message.content)}")
            # Save the response to JSON
            save_to_json(message.content[0].text)
            return message.content
        else:
            logger.error("API response missing content field")
            return False
            
    except ClientError as e:
        logger.error(f"API Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

# Example usage
if __name__ == "__main__":
    pdf_path = "/Users/and_seb/Documents/SiteSteer/Forms_Backend/pdfs/Toolbox Talk.pdf"
    prompt = "Please analyze this form and describe its structure."
    
    result = llm_call(prompt, pdf_path)
    if result:
        print(result)
    else:
        print("Error processing the PDF")