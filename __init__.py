import argparse
import base64
import json
import logging
import requests
from pathlib import Path

# Constants
API_KEY = "GEMINI_API_KEY"  # Replace with your actual API key
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={API_KEY}"
OUTPUT_RESPONSE_FILE = "response.txt"
LOG_FILE = "logs.txt"

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

def convert_image_to_base64(image_path):
    """Converts a JPEG image to a Base64-encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            logging.info(f"Successfully converted image at {image_path} to Base64.")
            return encoded_image
    except Exception as e:
        logging.error(f"Error converting image to Base64: {e}")
        raise

def send_image_to_gemini(encoded_image):
    """Sends the Base64-encoded image to Gemini 1.5 Pro and returns the response."""
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": "The object bound in the orange box has triggered the CCTV. Describe the scene in 120 characters. Do not mention time or date."},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_image
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(URL, headers=headers, json=data)
        response.raise_for_status()
        logging.info("Request sent to Gemini 1.5 Pro successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to Gemini 1.5 Pro: {e}")
        raise

def save_response_to_file(response, output_file):
    """Saves the value of 'text' from the response to a text file."""
    try:
        # Extract the text value
        text_value = response["candidates"][0]["content"]["parts"][0]["text"]
        
        # Save the extracted text to the file
        with open(output_file, "w") as file:
            file.write(text_value)
            logging.info(f"Extracted text saved to {output_file}.")
    except KeyError as e:
        logging.error(f"KeyError while extracting text: {e}")
        raise
    except Exception as e:
        logging.error(f"Error saving response to file: {e}")
        raise

def main(img_path):
    """Main function to send an image to Gemini 1.5 Pro and log the response."""
    try:
        # Ensure the image exists
        image_path = Path(img_path)
        if not image_path.is_file():
            logging.error(f"Image file not found: {img_path}")
            print(f"Error: Image file not found: {img_path}")
            return
        
        # Convert the image to Base64
        encoded_image = convert_image_to_base64(image_path)
        
        # Send the Base64 image to Gemini 1.5 Pro
        response = send_image_to_gemini(encoded_image)
        
        # Save the response to a text file
        save_response_to_file(response, OUTPUT_RESPONSE_FILE)
        
        print(f"Response saved to {OUTPUT_RESPONSE_FILE}. Check {LOG_FILE} for details.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"An error occurred. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Send a JPEG image to Gemini 1.5 Pro for scene description.")
    parser.add_argument("--img_path", required=True, help="Path to the JPEG image file.")
    args = parser.parse_args()

    # Run the main function with the provided image path
    main(args.img_path)
