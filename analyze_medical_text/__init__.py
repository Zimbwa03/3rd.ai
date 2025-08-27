import azure.functions as func
import json
import os
import pickle
import logging
from azure.storage.blob import BlobServiceClient

# Global variable to cache the model
model_package = None
medical_ai = Noneimport azure.functions as func
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


def load_model():
    """Load model from Azure Blob Storage"""
    try:
        logging.info("Loading model from Blob Storage...")
        
        # Check if connection string exists
        blob_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if not blob_connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set")
        
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_client = blob_service_client.get_container_client("models")
        
        # Use a more reliable temp path for Azure Functions
        local_path = os.path.join(os.getcwd(), "temp_model.pkl")
        
        # Download the model
        blob_client = container_client.get_blob_client("medical_ai_model_package.pkl")
        
        logging.info("Downloading model from blob storage...")
        with open(local_path, "wb") as f:
            blob_data = blob_client.download_blob()
            f.write(blob_data.readall())
        
        # Load the model
        logging.info("Loading model from file...")
        with open(local_path, "rb") as f:
            model_data = pickle.load(f)
        
        # Clean up temp file
        try:
            os.remove(local_path)
        except Exception as cleanup_error:
            logging.warning(f"Could not clean up temp file: {cleanup_error}")
        
        logging.info("Model loaded successfully.")
        return model_data
        
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        raise

def get_model():
    """Get or load the model (lazy loading with caching)"""
    global model_package, medical_ai
    
    if model_package is None:
        logging.info("Model not cached, loading...")
        model_package = load_model()
        medical_ai = model_package.get("medical_ai")
        
        if medical_ai is None:
            raise ValueError("medical_ai not found in model package")
    
    return medical_ai

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main Azure Function entry point"""
    try:
        logging.info("Function execution started")
        
        # Parse request body
        try:
            body = req.get_json()
            if body is None:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON in request body"}),
                    mimetype="application/json",
                    status_code=400
                )
        except Exception as json_error:
            logging.error(f"Error parsing JSON: {json_error}")
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON format"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Get text from request
        text = body.get("text", "")
        if not text or not text.strip():
            return func.HttpResponse(
                json.dumps({"error": "No text provided or text is empty"}),
                mimetype="application/json",
                status_code=400
            )
        
        logging.info(f"Analyzing text of length: {len(text)}")
        
        # Load model (lazy loading)
        try:
            ai_model = get_model()
        except Exception as model_error:
            logging.error(f"Failed to load model: {model_error}")
            return func.HttpResponse(
                json.dumps({"error": "Model loading failed", "details": str(model_error)}),
                mimetype="application/json",
                status_code=500
            )
        
        # Analyze the text
        try:
            result = ai_model.analyze_conversation(text)
            logging.info("Analysis completed successfully")
        except Exception as analysis_error:
            logging.error(f"Analysis failed: {analysis_error}")
            return func.HttpResponse(
                json.dumps({"error": "Analysis failed", "details": str(analysis_error)}),
                mimetype="application/json",
                status_code=500
            )
        
        # Return results
        return func.HttpResponse(
            json.dumps(result, default=str),  # default=str handles non-serializable objects
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Unexpected error in function execution: {str(e)}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error", 
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )

