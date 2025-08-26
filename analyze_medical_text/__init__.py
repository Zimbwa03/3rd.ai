import azure.functions as func
import json
import os
import pickle
import logging
from azure.storage.blob import BlobServiceClient

def load_model():
    try:
        logging.info("Loading model from Blob Storage...")
        blob_connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_client = blob_service_client.get_container_client("models")

        local_path = "/tmp/medical_ai_model_package.pkl"
        blob_client = container_client.get_blob_client("medical_ai_model_package.pkl")
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

        with open(local_path, "rb") as f:
            logging.info("Model loaded successfully.")
            return pickle.load(f)
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        raise

model_package = load_model()
medical_ai = model_package.get("medical_ai")

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        text = body.get("text", "")

        if not text:
            return func.HttpResponse(
                json.dumps({"error": "No text provided"}),
                mimetype="application/json",
                status_code=400
            )

        logging.info(f"Analyzing text: {text}")
        result = medical_ai.analyze_conversation(text)

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in function execution: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
