import uvicorn
import os

port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    uvicorn.run("backend.api_server_enhanced:app", host="0.0.0.0", port=port)
