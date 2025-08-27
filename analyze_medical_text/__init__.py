import azure.functions as func
import json
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test function to isolate the issue"""
    try:
        logging.info("=== FUNCTION STARTED ===")
        
        # Test 1: Basic response
        logging.info("Test 1: Function is working")
        
        # Test 2: Environment variables
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        logging.info(f"Test 2: Connection string exists: {connection_string is not None}")
        
        # Test 3: Get request parameters
        text = req.params.get('text', 'No text provided')
        method = req.method
        logging.info(f"Test 3: Method={method}, Text parameter={text}")
        
        # Test 4: Try blob storage connection (without downloading)
        blob_test_result = "Not tested"
        try:
            if connection_string:
                from azure.storage.blob import BlobServiceClient
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                # Just test the connection, don't download anything
                containers = list(blob_service_client.list_containers(max_results=1))
                blob_test_result = f"Connection successful, found containers: {len(containers)}"
            else:
                blob_test_result = "No connection string"
        except Exception as blob_error:
            blob_test_result = f"Blob connection failed: {str(blob_error)}"
        
        logging.info(f"Test 4: Blob storage test: {blob_test_result}")
        
        # Return test results
        response_data = {
            "status": "success",
            "message": "Test function working",
            "tests": {
                "function_working": True,
                "connection_string_exists": connection_string is not None,
                "request_method": method,
                "text_parameter": text,
                "blob_storage_test": blob_test_result
            }
        }
        
        logging.info("=== FUNCTION COMPLETED SUCCESSFULLY ===")
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"=== FUNCTION FAILED ===")
        logging.error(f"Error: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        
        # Get full traceback
        import traceback
        full_traceback = traceback.format_exc()
        logging.error(f"Full traceback: {full_traceback}")
        
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": full_traceback
            }, indent=2),
            mimetype="application/json",
            status_code=500
        )
