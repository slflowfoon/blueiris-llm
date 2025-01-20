#!/usr/bin/env python

import argparse
import base64
import json
import logging
import requests
import os
from pathlib import Path
from datetime import datetime, timedelta

API_KEY = "GEMINI_API_KEY"  # Replace with your actual API key
MODEL = "gemini-1.5-pro"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
OUTPUT_RESPONSE_FILE = "response.log"
LOG_FILE = "blueiris-llm.log"
LOG_RETENTION_DAYS = 30  # Keep logs for 30 days
AI_PROMPT = "Describe the objects in the scene"

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
        response = requests.post(URL, headers=headers, json=data)
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
            return
        
        text_value = response["candidates"][0]["content"]["parts"][0]["text"]
        
        with open(output_file, "w") as file:
            file.write(text_value)
            logging.info(f"Extracted text saved to {output_file}.")
    except KeyError as e:
        logging.error(f"KeyError while extracting text: {e}")
        raise
    except Exception as e:
        logging.error(f"Error saving response to file: {e}")
        raise

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

def main(img_path):
    try:
        image_path = Path(img_path)
        if not image_path.is_file():
            logging.error(f"Image file not found: {img_path}")
            print(f"Error: Image file not found: {img_path}")
            return
        
        encoded_image = convert_image_to_base64(image_path)
        
        response = send_image_to_gemini(encoded_image)
        
        save_response_to_file(response, OUTPUT_RESPONSE_FILE)

        delete_old_logs(LOG_FILE, LOG_RETENTION_DAYS)
        
        print(f"Response saved to {OUTPUT_RESPONSE_FILE}. Check {LOG_FILE} for details.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"An error occurred. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a JPEG image to Gemini for analysing.")
    parser.add_argument("--img_path", required=True, help="Path to the alert image file.")
    args = parser.parse_args()

    main(args.img_path)
