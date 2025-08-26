import azure.functions as func
import json
import os
import pickle
import logging
from azure.storage.blob import BlobServiceClient

# Local cache path inside Azure Functions (only /tmp is writable)
LOCAL_MODEL_PATH = "/tmp/medical_ai_model_package.pkl"

def load_model():
    try:
        # Use the default Function storage connection string
        blob_connection_string = os.environ["AzureWebJobsStorage"]
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_client = blob_service_client.get_container_client("models")

        # 🔎 Debug: list blobs in container
        logging.info("Listing blobs inside 'models' container...")
        blob_list = container_client.list_blobs()
        found_model = False
        for blob in blob_list:
            logging.info(f" - Found blob: {blob.name}")
            if blob.name == "medical_ai_model_package.pkl":
                found_model = True

        if not found_model:
            raise FileNotFoundError("medical_ai_model_package.pkl not found in 'models' container.")

        # Download only if not already cached
        if not os.path.exists(LOCAL_MODEL_PATH):
            logging.info("Downloading model from Blob Storage...")
            blob_client = container_client.get_blob_client("medical_ai_model_package.pkl")
            with open(LOCAL_MODEL_PATH, "wb") as f:
                f.write(blob_client.download_blob().readall())
            logging.info("✅ Model downloaded successfully.")

        # Load pickle
        with open(LOCAL_MODEL_PATH, "rb") as f:
            return pickle.load(f)

    except Exception as e:
        logging.error(f"❌ Error loading model: {str(e)}")
        raise

# Load model once at cold start
try:
    model_package = load_model()
    medical_ai = model_package.get("medical_ai", None)
    if not medical_ai:
        logging.error("❌ 'medical_ai' object not found in model_package!")
except Exception as e:
    logging.error(f"❌ Failed to initialize model at startup: {str(e)}")
    medical_ai = None

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        text = body.get("text", "")

        if not medical_ai:
            return func.HttpResponse(
                json.dumps({"error": "Model not loaded"}),
                mimetype="application/json",
                status_code=500
            )

        # Run model inference (synchronous call is fine unless your model is async)
        result = medical_ai.analyze_conversation(text)

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error in function execution: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
