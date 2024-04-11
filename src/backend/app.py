import uvicorn
import logging


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)    
    # Start the server
    uvicorn.run("main:app")