import azure.functions as func
import json
import os
import pickle
import logging
from azure.storage.blob import BlobServiceClient

# Try loading model once at startup
medical_ai = None

def load_model():
    try:
        logging.info("🔄 Attempting to load model from Blob Storage...")

        # Ensure the environment variable is set
        blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not blob_connection_string:
            logging.error("❌ Missing AZURE_STORAGE_CONNECTION_STRING in Application Settings")
            return None

        # Connect to container
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_client = blob_service_client.get_container_client("models")

        # Download file into /tmp (only writeable folder in Azure Functions)
        local_path = "/tmp/medical_ai_model_package.pkl"
        blob_client = container_client.get_blob_client("medical_ai_model_package.pkl")

        logging.info("⬇️ Downloading model blob...")
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())

        # Load pickle
        with open(local_path, "rb") as f:
            logging.info("✅ Model file loaded successfully.")
            return pickle.load(f)

    except Exception as e:
        logging.error(f"❌ Error while loading model: {e}")
        return None


# Load model package at startup
model_package = load_model()
if model_package and "medical_ai" in model_package:
    medical_ai = model_package["medical_ai"]
    logging.info("✅ medical_ai object is ready")
else:
    logging.warning("⚠️ medical_ai not found in model package")


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

        if not medical_ai:
            # Model didn’t load
            return func.HttpResponse(
                json.dumps({"error": "Model not loaded. Check Blob storage or pickle format."}),
                mimetype="application/json",
                status_code=500
            )

        # Call your model safely
        logging.info(f"Analyzing text: {text}")
        result = medical_ai.analyze_conversation(text)

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error in function execution: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
