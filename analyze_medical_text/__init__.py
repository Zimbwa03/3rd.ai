import azure.functions as func
import json
import os
import pickle
from azure.storage.blob import BlobServiceClient

# Download model once at startup
def load_model():
    blob_connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client("models")

    # Download the model file to temp storage
    local_path = "/tmp/medical_ai_model_package.pkl"
    blob_client = container_client.get_blob_client("medical_ai_model_package.pkl")
    with open(local_path, "wb") as f:
        f.write(blob_client.download_blob().readall())

    with open(local_path, "rb") as f:
        return pickle.load(f)

model_package = load_model()
medical_ai = model_package["medical_ai"]

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        text = body.get("text", "")

        result = medical_ai.analyze_conversation(text)
        return func.HttpResponse(json.dumps(result), mimetype="application/json", status_code=200)
    except Exception as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)
