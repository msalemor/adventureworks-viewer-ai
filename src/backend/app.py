import uvicorn
import logging

# Use this file mainly for easier debugging from VS Code
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)    
    # Start the server
    uvicorn.run("main:app")