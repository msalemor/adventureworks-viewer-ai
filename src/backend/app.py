import uvicorn
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)    
    uvicorn.run("main:app")