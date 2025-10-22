

# import logging
# import os
# from azure.core.credentials import AzureKeyCredential
# from azure.search.documents import SearchClient
# from azure.search.documents.indexes import SearchIndexClient
# from azure.search.documents.indexes.models import SearchIndex, SearchField
# from azure.search.documents.models import VectorQuery
# from dotenv import load_dotenv
# import base64
# from pathlib import Path
# import http.client
# import json
# import urllib.parse

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[logging.FileHandler('search_index.log'), logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)

# # Load environment variables
# load_dotenv()
# SERVICE_ENDPOINT = os.getenv("SERVICE_ENDPOINT", "").strip()
# SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY", "").strip()
# INDEX_NAME = os.getenv("INDEX_NAME", "").strip()
# AI_VISION_KEY = os.getenv("AZURE_AI_VISION_API_KEY", "").strip()
# AI_VISION_REGION = os.getenv("AZURE_AI_VISION_REGION", "").strip()
# AI_VISION_ENDPOINT = os.getenv("AZURE_AI_VISION_ENDPOINT", "").strip()
# DEFAULT_IMAGES_DIR = Path(os.getenv("IMAGES_DIR", "/images"))

# # Validate environment variables
# if not SERVICE_ENDPOINT:
#     logger.warning("SERVICE_ENDPOINT is not set in .env file, must be provided via function parameters")
# if not SERVICE_ENDPOINT.startswith("https://"):
#     logger.warning(f"Invalid SERVICE_ENDPOINT in .env: {SERVICE_ENDPOINT}. Must start with 'https://' if provided.")
# if not SEARCH_ADMIN_KEY:
#     logger.warning("SEARCH_ADMIN_KEY is not set in .env file, must be provided via function parameters")
# if not INDEX_NAME:
#     logger.warning("INDEX_NAME is not set in .env file, must be provided via function parameters")
# if not AI_VISION_KEY:
#     logger.warning("AI_VISION_KEY is not set in .env file, must be provided for image search")
# if not AI_VISION_REGION:
#     logger.warning("AI_VISION_REGION is not set in .env file, must be provided for image search")
# if not AI_VISION_ENDPOINT:
#     logger.warning("AI_VISION_ENDPOINT is not set in .env file, must be provided for image search")
# if not DEFAULT_IMAGES_DIR.exists():
#     logger.warning(f"IMAGES_DIR does not exist: {DEFAULT_IMAGES_DIR}")

# logger.info(f"Loaded SERVICE_ENDPOINT: {SERVICE_ENDPOINT}")
# logger.info(f"Loaded INDEX_NAME: {INDEX_NAME}")
# logger.info(f"Loaded SEARCH_ADMIN_KEY: {'*' * len(SEARCH_ADMIN_KEY)} (hidden)")
# logger.info(f"Loaded AI_VISION_KEY: {'*' * len(AI_VISION_KEY)} (hidden)")
# logger.info(f"Loaded AI_VISION_REGION: {AI_VISION_REGION}")
# logger.info(f"Loaded AI_VISION_ENDPOINT: {AI_VISION_ENDPOINT}")
# logger.info(f"Loaded IMAGES_DIR: {DEFAULT_IMAGES_DIR}")

# def _normalize_region(region: str) -> str:
#     """Normalize region format for AI Vision service (placeholder implementation)."""
#     return region.lower().replace(" ", "")

# def get_image_vector(image_path, key, region, endpoint=None):
#     """
#     Generate vector embedding for an image using Azure AI Vision service.
    
#     Args:
#         image_path (str or os.PathLike): Path or URL to the image.
#         key (str): Azure AI Vision subscription key.
#         region (str): Azure AI Vision service region.
#         endpoint (str, optional): Azure AI Vision endpoint (overrides region-based host if provided).
    
#     Returns:
#         list[float]: The image's vector embedding.
    
#     Raises:
#         Exception: If the API request fails or the response lacks a valid vector.
#     """
#     headers = {'Ocp-Apim-Subscription-Key': key}
#     params = urllib.parse.urlencode({'model-version': '2023-04-15'})
    
#     # Decide host
#     if endpoint and str(endpoint).strip():
#         parsed = urllib.parse.urlparse(str(endpoint).strip())
#         host = parsed.netloc
#         if not host:
#             raise Exception(f"Invalid AZURE_AI_VISION_ENDPOINT: {endpoint}")
#     else:
#         host = f"{region}.api.cognitive.microsoft.com"
    
#     # Decide body
#     if isinstance(image_path, (str, os.PathLike)) and str(image_path).startswith(("http://", "https://")):
#         headers['Content-Type'] = 'application/json'
#         body = json.dumps({"url": str(image_path)})
#     else:
#         headers['Content-Type'] = 'application/octet-stream'
#         with open(image_path, "rb") as f:
#             body = f.read()
    
#     conn = http.client.HTTPSConnection(host, timeout=10)
#     url_path = f"/computervision/retrieval:vectorizeImage?api-version=2024-02-01&{params}"
#     conn.request("POST", url_path, body, headers)
#     resp = conn.getresponse()
#     raw = resp.read()
    
#     try:
#         data = json.loads(raw.decode("utf-8")) if raw else {}
#     except Exception:
#         data = {"raw": raw[:200].decode("utf-8", errors="replace") if raw else ""}
    
#     conn.close()
    
#     if resp.status != 200:
#         msg = (isinstance(data, dict) and (data.get("message") or data.get("error") or data.get("code") or data.get("raw"))) or ""
#         raise Exception(f"Vision API {resp.status} {resp.reason}: {msg}")
    
#     vec = data.get("vector")
#     if not isinstance(vec, list):
#         raise Exception(f"No 'vector' in response for {image_path}")
    
#     logger.info(f"Generated vector for image: {image_path}")
#     return vec

# def create_index(index_name: str, fields: list[SearchField]):
#     """Create or update a search index with the specified name and fields."""
#     if not index_name:
#         logger.error("Index name is missing")
#         raise ValueError("Index name must be provided")
#     if not fields:
#         logger.error("No fields provided for index creation")
#         raise ValueError("Fields list must not be empty")

#     try:
#         index_client = SearchIndexClient(
#             endpoint=SERVICE_ENDPOINT.rstrip('/'),
#             credential=AzureKeyCredential(SEARCH_ADMIN_KEY)
#         )
#         index = SearchIndex(name=index_name, fields=fields)
#         index_client.create_or_update_index(index)
#         logger.info(f"Created or updated index: {index_name}")
#     except Exception as e:
#         logger.error(f"Error creating index {index_name}: {e}")
#         raise

# def retrieve_all_vectors(select_fields: list[str], endpoint: str = None, api_key: str = None, index_name: str = None):
#     """
#     Retrieve all documents from the specified Azure Cognitive Search index, including image vectors.
    
#     Args:
#         select_fields (list[str]): List of fields to retrieve (e.g., ['id', 'description', 'image_vector']).
#         endpoint (str, optional): Azure Cognitive Search service endpoint.
#         api_key (str, optional): API key for authentication.
#         index_name (str, optional): Name of the search index.
    
#     Returns:
#         list[dict]: List of dictionaries containing the retrieved documents.
#     """
#     if not select_fields:
#         logger.error("No select fields provided for retrieval")
#         return []

#     # Use provided parameters or fall back to environment variables
#     final_endpoint = endpoint.rstrip('/') if endpoint else SERVICE_ENDPOINT.rstrip('/')
#     final_api_key = api_key if api_key else SEARCH_ADMIN_KEY
#     final_index_name = index_name if index_name else INDEX_NAME

#     # Validate parameters
#     if not final_endpoint:
#         logger.error("Endpoint is missing")
#         return []
#     if not final_endpoint.startswith("https://"):
#         logger.error(f"Invalid endpoint: {final_endpoint}. Must start with 'https://'.")
#         return []
#     if not final_api_key:
#         logger.error("API key is missing")
#         return []
#     if not final_index_name:
#         logger.error("Index name is missing")
#         return []

#     try:
#         client = SearchClient(
#             endpoint=final_endpoint,
#             index_name=final_index_name,
#             credential=AzureKeyCredential(final_api_key)
#         )
#         logger.info(f"Initialized SearchClient for index: {final_index_name}")

#         entries = []
#         results = client.search(
#             search_text="*",
#             select=select_fields,
#             top=1000  # Batch size; adjust as needed
#         )
#         for doc in results:
#             entry = {
#                 field: (f"{doc[field][:200]}..." if isinstance(doc[field], str) and len(doc[field]) > 200 else doc[field])
#                 for field in select_fields
#             }
#             entries.append(entry)

#         # Handle pagination for large indexes
#         while results.get_continuation_token():
#             results = client.search(
#                 search_text="*",
#                 select=select_fields,
#                 top=1000,
#                 continuation_token=results.get_continuation_token()
#             )
#             for doc in results:
#                 entry = {
#                     field: (f"{doc[field][:200]}..." if isinstance(doc[field], str) and len(doc[field]) > 200 else doc[field])
#                     for field in select_fields
#                 }
#                 entries.append(entry)

#         if not entries:
#             logger.warning(f"No entries found in index: {final_index_name}")
#         else:
#             logger.info(f"Retrieved {len(entries)} entries from index: {final_index_name}")
#         return entries
#     except Exception as e:
#         logger.error(f"Error retrieving entries from index {final_index_name}: {e}")
#         return []

# # def search_index(query: str, select_fields: list[str], endpoint: str = None, api_key: str = None, index_name: str = None):
# #     """
# #     Search the specified Azure Cognitive Search index using a query and return results as a list of dictionaries.
    
# #     Args:
# #         query (str): The search query from the user.
# #         select_fields (list[str]): List of fields to retrieve from the index.
# #         endpoint (str, optional): Azure Cognitive Search service endpoint.
# #         api_key (str, optional): API key for authentication.
# #         index_name (str, optional): Name of the search index.
    
# #     Returns:
# #         list[dict]: List of dictionaries containing the search results.
# #     """
# #     if not query:
# #         logger.error("Search query is missing")
# #         return []
# #     if not select_fields:
# #         logger.error("No select fields provided for search query")
# #         return []

# #     final_endpoint = endpoint.rstrip('/') if endpoint else SERVICE_ENDPOINT.rstrip('/')
# #     final_api_key = api_key if api_key else SEARCH_ADMIN_KEY
# #     final_index_name = index_name if index_name else INDEX_NAME

# #     if not final_endpoint:
# #         logger.error("Endpoint is missing")
# #         return []
# #     if not final_endpoint.startswith("https://"):
# #         logger.error(f"Invalid endpoint: {final_endpoint}. Must start with 'https://'.")
# #         return []
# #     if not final_api_key:
# #         logger.error("API key is missing")
# #         return []
# #     if not final_index_name:
# #         logger.error("Index name is missing")
# #         return []

# #     try:
# #         client = SearchClient(
# #             endpoint=final_endpoint,
# #             index_name=final_index_name,
# #             credential=AzureKeyCredential(final_api_key)
# #         )
# #         logger.info(f"Initialized SearchClient for index: {final_index_name}")
# #         results = client.search(
# #             search_text=query,
# #             select=select_fields,
# #             top=10
# #         )
# #         entries = []
# #         for doc in results:
# #             entry = {
# #                 field: (f"{doc[field][:200]}..." if isinstance(doc[field], str) and len(doc[field]) > 200 else doc[field])
# #                 for field in select_fields
# #             }
# #             entries.append(entry)
# #         if not entries:
# #             logger.warning(f"No entries found for query '{query}' in index: {final_index_name}")
# #         else:
# #             logger.info(f"Found {len(entries)} entries for query '{query}' in index: {final_index_name}")
# #         return entries
# #     except Exception as e:
# #         logger.error(f"Error searching index {final_index_name} with query '{query}': {e}")
# #         return []

# def search_similar(query_image_path: str, k: int = 3, index_name: str = INDEX_NAME, images_dir: Path = DEFAULT_IMAGES_DIR, vision_key: str = None, vision_region: str = None, vision_endpoint: str = None):
#     """
#     Search for images similar to the query image in the specified Azure Cognitive Search index using vector search.
    
#     Args:
#         query_image_path (str): Path to the query image file.
#         k (int, optional): Number of similar images to return (default: 3).
#         index_name (str, optional): Name of the search index (default: INDEX_NAME).
#         images_dir (Path, optional): Directory containing images (default: DEFAULT_IMAGES_DIR).
#         vision_key (str, optional): AI Vision service key (default: AI_VISION_KEY).
#         vision_region (str, optional): AI Vision service region (default: AI_VISION_REGION).
#         vision_endpoint (str, optional): AI Vision service endpoint (default: AI_VISION_ENDPOINT).
    
#     Returns:
#         list[dict]: List of dictionaries containing metadata for similar images.
#     """
#     if not query_image_path:
#         logger.error("Query image path is missing")
#         return []
#     if not Path(query_image_path).exists():
#         logger.error(f"Query image does not exist: {query_image_path}")
#         return []
#     if k <= 0:
#         logger.error("k must be a positive integer")
#         return []

#     final_index_name = index_name if index_name else INDEX_NAME
#     final_vision_key = vision_key if vision_key else AI_VISION_KEY
#     final_vision_region = vision_region if vision_region else AI_VISION_REGION
#     final_vision_endpoint = vision_endpoint if vision_endpoint else AI_VISION_ENDPOINT

#     if not final_index_name:
#         logger.error("Index name is missing")
#         return []
#     if not final_vision_key:
#         logger.error("AI Vision key is missing")
#         return []
#     if not final_vision_region:
#         logger.error("AI Vision region is missing")
#         return []
#     if not final_vision_endpoint:
#         logger.error("AI Vision endpoint is missing")
#         return []

#     try:
#         cred = AzureKeyCredential(SEARCH_ADMIN_KEY)
#         sc = SearchClient(endpoint=SERVICE_ENDPOINT.rstrip('/'), index_name=final_index_name, credential=cred)
#         logger.info(f"Initialized SearchClient for index: {final_index_name}")

#         vec = get_image_vector(query_image_path, final_vision_key, _normalize_region(final_vision_region), final_vision_endpoint)

#         vq = VectorQuery(k_nearest_neighbors=k, fields="image_vector")
#         vq.enable_additional_properties_sending()
#         vq.additional_properties["vector"] = vec
#         vq.additional_properties["kind"] = "vector"

#         results = []
#         for r in sc.search(search_text=None, vector_queries=[vq], select=["id", "description"]):
#             try:
#                 decoded = base64.urlsafe_b64decode(r["id"]).decode("utf-8")
#             except Exception:
#                 decoded = r["id"]
#             candidate_path = images_dir / decoded
#             results.append({
#                 "description": r.get("description"),
#                 "decoded_path": str(candidate_path),
#                 "exists": candidate_path.exists(),
#                 "score": r.get("@search.score")
#             })
#         if not results:
#             logger.warning(f"No similar images found for query image '{query_image_path}' in index: {final_index_name}")
#         else:
#             logger.info(f"Found {len(results)} similar images for query image '{query_image_path}' in index: {final_index_name}")
#         return results
#     except Exception as e:
#         logger.error(f"Error searching index {final_index_name} for similar images: {e}")
#         return []
    

# # def main(input_file: str, results_dir: str = "/Users/kavyanegi/Downloads/MCP/results"):
# #     """
# #     Read an image path from the input file and perform a similarity search, saving results to a folder.
# #     Args:
# #         input_file (str): Path to a text file containing the query image path.
# #         results_dir (str, optional): Directory to save the results (default: /Users/kavyanegi/Downloads/MCP/results).
# #     Returns:
# #         str: Path to the results folder.
# #     """
# #     # Validate input file
# #     if not input_file:
# #         logger.error("Input file path is missing")
# #         raise ValueError("Input file path must be provided")
# #     input_path = Path(input_file)
# #     if not input_path.exists():
# #         logger.error(f"Input file does not exist: {input_file}")
# #         raise FileNotFoundError(f"Input file does not exist: {input_file}")

# #     # Read image path from file
# #     try:
# #         with open(input_path, "r") as f:
# #             query_image_path = f.read().strip()
# #         logger.info(f"Read query image path: {query_image_path}")
# #     except Exception as e:
# #         logger.error(f"Error reading input file {input_file}: {e}")
# #         raise

# #     # Validate query image path
# #     if not query_image_path:
# #         logger.error("Query image path is empty in input file")
# #         raise ValueError("Query image path is empty")
# #     if not Path(query_image_path).exists():
# #         logger.error(f"Query image does not exist: {query_image_path}")
# #         raise FileNotFoundError(f"Query image does not exist: {query_image_path}")

# #     # Validate results directory
# #     results_path = Path(results_dir)
# #     if results_path.is_file():
# #         logger.error(f"Results directory path points to a file, not a directory: {results_dir}")
# #         raise ValueError(f"Results directory path points to a file, not a directory: {results_dir}")
    
# #     # Create results directory
# #     results_path.mkdir(parents=True, exist_ok=True)
# #     logger.info(f"Ensured results directory exists: {results_dir}")

# #     # Perform similarity search
# #     try:
# #         results = search_similar(
# #             query_image_path=query_image_path,
# #             k=3,
# #             index_name=INDEX_NAME,
# #             images_dir=DEFAULT_IMAGES_DIR
# #         )
# #         logger.info(f"Similarity search completed for image: {query_image_path}")
# #     except Exception as e:
# #         logger.error(f"Error performing similarity search: {e}")
# #         raise

# #     # Save results to JSON file
# #     output_file = results_path / "results.json"
# #     try:
# #         with open(output_file, "w") as f:
# #             json.dump(results, f, indent=4)
# #         logger.info(f"Saved results to: {output_file}")
# #     except Exception as e:
# #         logger.error(f"Error saving results to {output_file}: {e}")
# #         raise

# #     return str(results_path)


# def main(input_file: str, results_dir: str = "/Users/kavyanegi/Downloads/MCP/results"):
#     """
#     Read an image path from the input file and perform a similarity search, saving results to a folder.
#     Args:
#         input_file (str): Path to a text file containing the query image path.
#         results_dir (str, optional): Directory to save the results.
#     Returns:
#         str: Path to the results folder.
#     """
#     logger.info(f"Starting main with input_file={input_file}, results_dir={results_dir}")
    
#     # Validate input file
#     logger.info("Validating input file")
#     if not input_file:
#         logger.error("Input file path is missing")
#         raise ValueError("Input file path must be provided")
#     input_path = Path(input_file)
#     logger.info(f"Checking if input file exists: {input_path}")
#     if not input_path.exists():
#         logger.error(f"Input file does not exist: {input_file}")
#         raise FileNotFoundError(f"Input file does not exist: {input_file}")

#     # Read image path from file
#     logger.info("Reading input file")
#     try:
#         with open(input_path, "r") as f:
#             query_image_path = f.read().strip()
#         logger.info(f"Read query image path: {query_image_path}")
#     except Exception as e:
#         logger.error(f"Error reading input file {input_file}: {e}")
#         raise

#     # Validate query image path
#     logger.info("Validating query image path")
#     if not query_image_path:
#         logger.error("Query image path is empty in input file")
#         raise ValueError("Query image path is empty")
#     query_image_path = Path(query_image_path)
#     logger.info(f"Checking if query image exists: {query_image_path}")
#     if not query_image_path.exists():
#         logger.error(f"Query image does not exist: {query_image_path}")
#         raise FileNotFoundError(f"Query image does not exist: {query_image_path}")

#     # Validate results directory
#     logger.info("Validating results directory")
#     results_path = Path(results_dir)
#     logger.info(f"Checking if results path is a file: {results_path}")
#     if results_path.exists() and results_path.is_file():
#         logger.error(f"Results directory path points to a file, not a directory: {results_dir}")
#         raise ValueError(f"Results directory path points to a file, not a directory: {results_dir}")

#     # Create results directory
#     logger.info("Creating results directory")
#     try:
#         results_path.mkdir(parents=True, exist_ok=True)
#         logger.info(f"Ensured results directory exists: {results_dir}")
#     except Exception as e:
#         logger.error(f"Error creating results directory {results_dir}: {e}")
#         raise

#     # Perform similarity search
#     logger.info("Performing similarity search")
#     try:
#         results = search_similar(
#             query_image_path=str(query_image_path),
#             k=5,
#             index_name=INDEX_NAME,
#             images_dir=DEFAULT_IMAGES_DIR
#         )
#         logger.info(f"Similarity search completed for image: {query_image_path}")
#     except Exception as e:
#         logger.error(f"Error performing similarity search: {e}")
#         raise

#     # Save results to JSON file
#     logger.info("Saving results to JSON")
#     output_file = results_path / "results.json"
#     try:
#         with open(output_file, "w") as f:
#             json.dump(results, f, indent=4)
#         logger.info(f"Saved results to: {output_file}")
#     except Exception as e:
#         logger.error(f"Error saving results to {output_file}: {e}")
#         raise

#     return str(results_path)

# if __name__ == "__main__":
#     import sys
#     logger.info(f"Script started with arguments: {sys.argv}")
#     if len(sys.argv) != 2:
#         logger.error("Invalid number of arguments")
#         print("Usage: python azure_aisearch.py <input_file>")
#         sys.exit(1)
#     main(sys.argv[1])




import logging
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SearchField
from azure.search.documents.models import VectorQuery
from dotenv import load_dotenv
import base64
from pathlib import Path
import http.client
import json
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('search_index.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
# Note: SERVICE_ENDPOINT, SEARCH_ADMIN_KEY, INDEX_NAME, and IMAGES_DIR are set from UI (credentials.json)
# AI Vision credentials (API_KEY, REGION, ENDPOINT) should be in .env file
load_dotenv()

# These come from UI via credentials.json → server.py → environment variables
SERVICE_ENDPOINT = os.getenv("SERVICE_ENDPOINT", "").strip()
SEARCH_ADMIN_KEY = os.getenv("SEARCH_ADMIN_KEY", "").strip()
INDEX_NAME = os.getenv("INDEX_NAME", "").strip()
IMAGES_DIR_STR = os.getenv("IMAGES_DIR", "").strip()

# These should be in .env file
AI_VISION_KEY = os.getenv("AZURE_AI_VISION_API_KEY", "").strip()
AI_VISION_REGION = os.getenv("AI_VISION_REGION", "").strip()
AI_VISION_ENDPOINT = os.getenv("AI_VISION_ENDPOINT", "").strip()

# Set default images directory
DEFAULT_IMAGES_DIR = Path(IMAGES_DIR_STR) if IMAGES_DIR_STR else Path.cwd() / "images"

# Validate UI-provided credentials (these must be present)
if not SERVICE_ENDPOINT:
    logger.error("SERVICE_ENDPOINT is not set. Must be provided via UI credentials.")
elif not SERVICE_ENDPOINT.startswith("https://"):
    logger.error(f"Invalid SERVICE_ENDPOINT: {SERVICE_ENDPOINT}. Must start with 'https://'.")
else:
    logger.info(f"✓ Loaded SERVICE_ENDPOINT: {SERVICE_ENDPOINT}")

if not SEARCH_ADMIN_KEY:
    logger.error("SEARCH_ADMIN_KEY is not set. Must be provided via UI credentials.")
else:
    logger.info(f"✓ Loaded SEARCH_ADMIN_KEY: {'*' * len(SEARCH_ADMIN_KEY)} (hidden)")

if not INDEX_NAME:
    logger.error("INDEX_NAME is not set. Must be provided via UI credentials.")
else:
    logger.info(f"✓ Loaded INDEX_NAME: {INDEX_NAME}")

# Validate .env file credentials (these are optional for basic search, required for image vectorization)
if not AI_VISION_KEY:
    logger.warning("⚠ AI_VISION_KEY is not set in .env file. Image vectorization will not work.")
else:
    logger.info(f"✓ Loaded AI_VISION_KEY: {'*' * len(AI_VISION_KEY)} (hidden)")

if not AI_VISION_REGION:
    logger.warning("⚠ AI_VISION_REGION is not set in .env file. Image vectorization will not work.")
else:
    logger.info(f"✓ Loaded AI_VISION_REGION: {AI_VISION_REGION}")

if not AI_VISION_ENDPOINT:
    logger.warning("⚠ AI_VISION_ENDPOINT is not set in .env file. Will use region-based endpoint.")
else:
    logger.info(f"✓ Loaded AI_VISION_ENDPOINT: {AI_VISION_ENDPOINT}")

# Validate images directory
if not DEFAULT_IMAGES_DIR.exists():
    logger.warning(f"⚠ IMAGES_DIR does not exist: {DEFAULT_IMAGES_DIR}. Will be created if needed.")
else:
    logger.info(f"✓ Loaded IMAGES_DIR: {DEFAULT_IMAGES_DIR}")

def _normalize_region(region: str) -> str:
    """Normalize region format for AI Vision service (placeholder implementation)."""
    return region.lower().replace(" ", "")

def get_image_vector(image_path, key, region, endpoint=None):
    """
    Generate vector embedding for an image using Azure AI Vision service.
    
    Args:
        image_path (str or os.PathLike): Path or URL to the image.
        key (str): Azure AI Vision subscription key.
        region (str): Azure AI Vision service region.
        endpoint (str, optional): Azure AI Vision endpoint (overrides region-based host if provided).
    
    Returns:
        list[float]: The image's vector embedding.
    
    Raises:
        Exception: If the API request fails or the response lacks a valid vector.
    """
    headers = {'Ocp-Apim-Subscription-Key': key}
    params = urllib.parse.urlencode({'model-version': '2023-04-15'})
    
    # Decide host
    if endpoint and str(endpoint).strip():
        parsed = urllib.parse.urlparse(str(endpoint).strip())
        host = parsed.netloc
        if not host:
            raise Exception(f"Invalid AZURE_AI_VISION_ENDPOINT: {endpoint}")
    else:
        host = f"{region}.api.cognitive.microsoft.com"
    
    # Decide body
    if isinstance(image_path, (str, os.PathLike)) and str(image_path).startswith(("http://", "https://")):
        headers['Content-Type'] = 'application/json'
        body = json.dumps({"url": str(image_path)})
    else:
        headers['Content-Type'] = 'application/octet-stream'
        with open(image_path, "rb") as f:
            body = f.read()
    
    conn = http.client.HTTPSConnection(host, timeout=10)
    url_path = f"/computervision/retrieval:vectorizeImage?api-version=2024-02-01&{params}"
    conn.request("POST", url_path, body, headers)
    resp = conn.getresponse()
    raw = resp.read()
    
    try:
        data = json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        data = {"raw": raw[:200].decode("utf-8", errors="replace") if raw else ""}
    
    conn.close()
    
    if resp.status != 200:
        msg = (isinstance(data, dict) and (data.get("message") or data.get("error") or data.get("code") or data.get("raw"))) or ""
        raise Exception(f"Vision API {resp.status} {resp.reason}: {msg}")
    
    vec = data.get("vector")
    if not isinstance(vec, list):
        raise Exception(f"No 'vector' in response for {image_path}")
    
    logger.info(f"Generated vector for image: {image_path}")
    return vec

def create_index(index_name: str, fields: list[SearchField]):
    """Create or update a search index with the specified name and fields."""
    if not index_name:
        logger.error("Index name is missing")
        raise ValueError("Index name must be provided")
    if not fields:
        logger.error("No fields provided for index creation")
        raise ValueError("Fields list must not be empty")

    try:
        index_client = SearchIndexClient(
            endpoint=SERVICE_ENDPOINT.rstrip('/'),
            credential=AzureKeyCredential(SEARCH_ADMIN_KEY)
        )
        index = SearchIndex(name=index_name, fields=fields)
        index_client.create_or_update_index(index)
        logger.info(f"Created or updated index: {index_name}")
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {e}")
        raise

def retrieve_all_vectors(select_fields: list[str], endpoint: str = None, api_key: str = None, index_name: str = None):
    """
    Retrieve all documents from the specified Azure Cognitive Search index, including image vectors.
    
    Args:
        select_fields (list[str]): List of fields to retrieve (e.g., ['id', 'description', 'image_vector']).
        endpoint (str, optional): Azure Cognitive Search service endpoint.
        api_key (str, optional): API key for authentication.
        index_name (str, optional): Name of the search index.
    
    Returns:
        list[dict]: List of dictionaries containing the retrieved documents.
    """
    if not select_fields:
        logger.error("No select fields provided for retrieval")
        return []

    # Use provided parameters or fall back to environment variables
    final_endpoint = endpoint.rstrip('/') if endpoint else SERVICE_ENDPOINT.rstrip('/')
    final_api_key = api_key if api_key else SEARCH_ADMIN_KEY
    final_index_name = index_name if index_name else INDEX_NAME

    # Validate parameters
    if not final_endpoint:
        logger.error("Endpoint is missing")
        return []
    if not final_endpoint.startswith("https://"):
        logger.error(f"Invalid endpoint: {final_endpoint}. Must start with 'https://'.")
        return []
    if not final_api_key:
        logger.error("API key is missing")
        return []
    if not final_index_name:
        logger.error("Index name is missing")
        return []

    try:
        client = SearchClient(
            endpoint=final_endpoint,
            index_name=final_index_name,
            credential=AzureKeyCredential(final_api_key)
        )
        logger.info(f"Initialized SearchClient for index: {final_index_name}")

        entries = []
        results = client.search(
            search_text="*",
            select=select_fields,
            top=1000  # Batch size; adjust as needed
        )
        for doc in results:
            entries.append(doc)
        logger.info(f"Retrieved {len(entries)} documents from index: {final_index_name}")
        return entries
    except Exception as e:
        logger.error(f"Error retrieving vectors from index {final_index_name}: {e}")
        return []

async def search_similar(
    query_image_path: str,
    k: int = 5,
    index_name: str = None,
    images_dir = None,
    endpoint: str = None,
    api_key: str = None,
    ai_vision_key: str = None,
    ai_vision_region: str = None,
    ai_vision_endpoint: str = None
):
    """
    Search for similar images in Azure Cognitive Search using a query image.
    
    Args:
        query_image_path (str): Path or URL to the query image.
        k (int): Number of similar results to return (default: 5).
        index_name (str, optional): Name of the search index.
        images_dir (str or Path, optional): Directory containing indexed images.
        endpoint (str, optional): Azure Search endpoint.
        api_key (str, optional): Azure Search API key.
        ai_vision_key (str, optional): Azure AI Vision API key.
        ai_vision_region (str, optional): Azure AI Vision region.
        ai_vision_endpoint (str, optional): Azure AI Vision endpoint.
    
    Returns:
        list[dict]: List of similar images with metadata.
    """
    # Use provided parameters or fall back to environment variables
    final_endpoint = endpoint.rstrip('/') if endpoint else SERVICE_ENDPOINT.rstrip('/')
    final_api_key = api_key if api_key else SEARCH_ADMIN_KEY
    final_index_name = index_name if index_name else INDEX_NAME
    final_ai_vision_key = ai_vision_key if ai_vision_key else AI_VISION_KEY
    final_ai_vision_region = ai_vision_region if ai_vision_region else AI_VISION_REGION
    final_ai_vision_endpoint = ai_vision_endpoint if ai_vision_endpoint else AI_VISION_ENDPOINT
    
    # Handle images_dir
    if images_dir is None:
        images_dir = DEFAULT_IMAGES_DIR
    images_dir = Path(images_dir)

    # Validate required parameters
    if not final_endpoint:
        logger.error("Search endpoint is missing")
        return []
    if not final_endpoint.startswith("https://"):
        logger.error(f"Invalid endpoint: {final_endpoint}. Must start with 'https://'.")
        return []
    if not final_api_key:
        logger.error("Search API key is missing")
        return []
    if not final_index_name:
        logger.error("Index name is missing")
        return []
    if not final_ai_vision_key:
        logger.error("AI Vision API key is missing - cannot vectorize query image")
        return []
    if not final_ai_vision_region and not final_ai_vision_endpoint:
        logger.error("AI Vision region or endpoint must be provided")
        return []

    try:
        # Generate vector for query image
        logger.info(f"Generating vector for query image: {query_image_path}")
        vec = get_image_vector(
            query_image_path,
            key=final_ai_vision_key,
            region=final_ai_vision_region,
            endpoint=final_ai_vision_endpoint
        )

        # Create search client
        sc = SearchClient(
            endpoint=final_endpoint,
            index_name=final_index_name,
            credential=AzureKeyCredential(final_api_key)
        )

        # Perform vector search
        vq = VectorQuery(k_nearest_neighbors=k, fields="image_vector")
        vq.enable_additional_properties_sending()
        vq.additional_properties["vector"] = vec
        vq.additional_properties["kind"] = "vector"

        results = []
        for r in sc.search(search_text=None, vector_queries=[vq], select=["id", "description"]):
            try:
                decoded = base64.urlsafe_b64decode(r["id"]).decode("utf-8")
            except Exception:
                decoded = r["id"]
            candidate_path = images_dir / decoded
            results.append({
                "description": r.get("description"),
                "decoded_path": str(candidate_path),
                "exists": candidate_path.exists(),
                "score": r.get("@search.score")
            })
        if not results:
            logger.warning(f"No similar images found for query image '{query_image_path}' in index: {final_index_name}")
        else:
            logger.info(f"Found {len(results)} similar images for query image '{query_image_path}' in index: {final_index_name}")
        return results
    except Exception as e:
        logger.error(f"Error searching index {final_index_name} for similar images: {e}")
        return []


def main(input_file: str, results_dir: str = "/Users/kavyanegi/Downloads/MCP/results"):
    """
    Read an image path from the input file and perform a similarity search, saving results to a folder.
    Args:
        input_file (str): Path to a text file containing the query image path.
        results_dir (str, optional): Directory to save the results.
    Returns:
        str: Path to the results folder.
    """
    logger.info(f"Starting main with input_file={input_file}, results_dir={results_dir}")
    
    # Validate input file
    logger.info("Validating input file")
    if not input_file:
        logger.error("Input file path is missing")
        raise ValueError("Input file path must be provided")
    input_path = Path(input_file)
    logger.info(f"Checking if input file exists: {input_path}")
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_file}")
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    # Read image path from file
    logger.info("Reading input file")
    try:
        with open(input_path, "r") as f:
            query_image_path = f.read().strip()
        logger.info(f"Read query image path: {query_image_path}")
    except Exception as e:
        logger.error(f"Error reading input file {input_file}: {e}")
        raise

    # Validate query image path
    logger.info("Validating query image path")
    if not query_image_path:
        logger.error("Query image path is empty in input file")
        raise ValueError("Query image path is empty")
    query_image_path = Path(query_image_path)
    logger.info(f"Checking if query image exists: {query_image_path}")
    if not query_image_path.exists():
        logger.error(f"Query image does not exist: {query_image_path}")
        raise FileNotFoundError(f"Query image does not exist: {query_image_path}")

    # Validate results directory
    logger.info("Validating results directory")
    results_path = Path(results_dir)
    logger.info(f"Checking if results path is a file: {results_path}")
    if results_path.exists() and results_path.is_file():
        logger.error(f"Results directory path points to a file, not a directory: {results_dir}")
        raise ValueError(f"Results directory path points to a file, not a directory: {results_dir}")

    # Create results directory
    logger.info("Creating results directory")
    try:
        results_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured results directory exists: {results_dir}")
    except Exception as e:
        logger.error(f"Error creating results directory {results_dir}: {e}")
        raise

    # Perform similarity search
    logger.info("Performing similarity search")
    try:
        import asyncio
        results = asyncio.run(search_similar(
            query_image_path=str(query_image_path),
            k=5,
            index_name=INDEX_NAME,
            images_dir=DEFAULT_IMAGES_DIR
        ))
        logger.info(f"Similarity search completed for image: {query_image_path}")
    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
        raise

    # Save results to JSON file
    logger.info("Saving results to JSON")
    output_file = results_path / "results.json"
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
        logger.info(f"Saved results to: {output_file}")
    except Exception as e:
        logger.error(f"Error saving results to {output_file}: {e}")
        raise

    return str(results_path)

if __name__ == "__main__":
    import sys
    logger.info(f"Script started with arguments: {sys.argv}")
    if len(sys.argv) != 2:
        logger.error("Invalid number of arguments")
        print("Usage: python azure_aisearch.py <input_file>")
        sys.exit(1)
    main(sys.argv[1])