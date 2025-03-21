from io import BytesIO
from fastapi import FastAPI, File
from typing import Annotated

# Create the FastAPI app
app: FastAPI = FastAPI()

@app.get("/")
def get_main():
    """get_prediction listens for a POST request to /predict and
    returns the results of the AI classification of that image.
    The POST content must contain { "image": bytes[] } or the function will return 422 error.
    """

    return {"hello world"}
