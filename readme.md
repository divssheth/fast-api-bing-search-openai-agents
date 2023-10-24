# To execute the code you need to set the below environment variables
- AZURE_COSMOSDB_ENDPOINT
- AZURE_COSMOSDB_NAME
- AZURE_COSMOSDB_CONTAINER_NAME
- AZURE_COMOSDB_CONNECTION_STRING
- OPENAI_API_BASE
- OPENAI_API_KEY
- OPENAI_API_VERSION:2023-05-15,
- OPENAI_API_TYPE:azure,
- BING_SUBSCRIPTION_KEY
- BING_SEARCH_URL: https://api.bing.microsoft.com/v7.0/search

# Steps to execute code 
1. Install all dependencies in the requirements.txt - `pip install -r requirements.txt`
2. Execute main.py - `uvicorn min:app`

## Sample API call 
http://127.0.0.1:8000/message/{user_id}/{session_id}?question=What is your name?

user_id and session_id are currently random numbers, they are used for state management and tracking conversation. 