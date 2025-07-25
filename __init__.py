#!/usr/bin/env python

import argparse
import base64
import json
import logging
import requests
import os
from pathlib import Path
from datetime import datetime, timedelta

# Constants for Gemini AI
API_KEY = "GEMINI_API_KEY"  # Replace with your actual API key for Gemini
MODEL = "gemini-2.0-flash-lite"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
AI_PROMPT = "Describe the objects in the scene"

# Constants for Telegram
TELEGRAM_BOT_TOKEN = "REPLACE_WITH_BOT_API_KEY"  # Replace with your actual Telegram Bot API Key
CHAT_ID = "REPLACE_WITH_CHAT_ID"  # Replace with your actual Telegram Chat ID
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

# File paths and logging
OUTPUT_RESPONSE_FILE = "response.log"
LOG_FILE = "blueiris-llm.log"
LOG_RETENTION_DAYS = 30  # Keep logs for 30 days

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def convert_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            logging.info(f"Successfully converted image at {image_path} to Base64.")
            return encoded_image
    except Exception as e:
        logging.error(f"Error converting image to Base64: {e}")
        raise

def send_image_to_gemini(encoded_image):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": AI_PROMPT},
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
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        if response.status_code == 429:
            with open(OUTPUT_RESPONSE_FILE, "w") as file:
                file.write("429 error: Quota limit reached.")
            logging.warning("Received 429 error: Quota limit reached.")
            return None
        response.raise_for_status()
        logging.info(f"Request sent to {MODEL} successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request to {MODEL}: {e}")
        raise

def save_response_to_file(response, output_file):
    try:
        if response is None:
            logging.warning("No response from Gemini to save.")
            return None
        
        text_value = response["candidates"][0]["content"]["parts"][0]["text"]
        
        with open(output_file, "w") as file:
            file.write(text_value)
            logging.info(f"Extracted text saved to {output_file}.")
        return text_value
    except KeyError as e:
        logging.error(f"KeyError while extracting text: {e}")
        raise
    except Exception as e:
        logging.error(f"Error saving response to file: {e}")
        raise

def send_telegram_message_and_photo(api_url, chat_id, text_response, img_path):
    try:
        if not Path(img_path).is_file():
            logging.error(f"Telegram: Image file not found at {img_path}")
            return False

        files = {'photo': open(img_path, 'rb')}
        data = {'chat_id': chat_id, 'caption': text_response}

        response = requests.post(api_url, files=files, data=data)
        response.raise_for_status()

        logging.info("Telegram: Message and Photo sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Telegram: Error sending message and photo: {e}")
        return False
    except Exception as e:
        logging.error(f"Telegram: An unexpected error has occurred: {e}")
        return False

def delete_old_logs(log_file, retention_days):
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    try:
        log_file_path = Path(log_file)
        if log_file_path.is_file():
            file_modified_time = datetime.fromtimestamp(log_file_path.stat().st_mtime)
            if file_modified_time < cutoff_date:
                os.remove(log_file)
                logging.info(f"Deleted old log file: {log_file}")
        else:
            logging.warning(f"Log file not found at {log_file}")
    except Exception as e:
        logging.error(f"Error deleting old log file: {e}")

def main(img_path, send_to_telegram):
    try:
        image_path = Path(img_path)
        if not image_path.is_file():
            logging.error(f"Image file not found: {img_path}")
            print(f"Error: Image file not found: {img_path}")
            return
        
        encoded_image = convert_image_to_base64(image_path)
        
        response_json = send_image_to_gemini(encoded_image)
        
        extracted_text = save_response_to_file(response_json, OUTPUT_RESPONSE_FILE)

        if send_to_telegram and extracted_text:
            logging.info("Attempting to send message and photo to Telegram.")
            send_telegram_message_and_photo(TELEGRAM_API_URL, CHAT_ID, extracted_text, img_path)
        elif send_to_telegram and not extracted_text:
            logging.warning("Telegram sending skipped: No text response was extracted from Gemini.")

        delete_old_logs(LOG_FILE, LOG_RETENTION_DAYS)
        
        print(f"Processing complete. Response saved to {OUTPUT_RESPONSE_FILE}. Check {LOG_FILE} for details.")
    except Exception as e:
        logging.error(f"Unexpected error in main: {e}")
        print(f"An error occurred. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a JPEG image to Gemini for scene description and optionally to Telegram.")
    parser.add_argument("--img_path", required=True, help="Path to the JPEG image file.")
    parser.add_argument("--telegram", action="store_true", help="Send notification to Telegram.")
    args = parser.parse_args()

    main(args.img_path, args.telegram)
