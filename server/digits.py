"""
digits is a FastAPI app that hosts a Keras classification model for handwritten digits.

Usage: fastapi run digits.py

Will auto-create OpenAPI docs at /redoc

This file should be compliant with Pyright.
The tensorflow import is ignored with # type: ignore[import]
because tensorflow doesn't support type hints appropriately.
"""

from tensorflow.keras.saving import load_model  # type: ignore[import]
from PIL import Image
from io import BytesIO
import numpy as np
from fastapi import FastAPI, File
from typing import Annotated


model_path: str = "digits.keras"
# TODO: Use load_model that's imported above to open saved Keras model as global variable. NO TYPE HINT REQUIRED!

# Create the FastAPI app
app: FastAPI = FastAPI()


def image_to_np(image_bytes: bytes) -> np.ndarray:
    """image_to_np converts an image as bytes to proper numpy array via Pillow.
    It also reshapes the image to ensure that it's the shape the Keras model expects."""
    # First must use pillow to process bytes
    img = Image.open(BytesIO(image_bytes))
    # TODO: convert image to grayscale and resize
    # TODO: convert image to numpy array of shape model expects
    return None  # TODO: replace with np array so Pyright stops complaining


@app.post("/predict")
def get_prediction(image: Annotated[bytes, File()]) -> dict[str, int]:
    """get_prediction listens for a POST request to /predict and
    returns the results of the AI classification of that image.
    The POST content must contain { "image": bytes[] } or the function will return 422 error.
    """

    # Convert the bytes image into a format our model can use
    processed_image = image_to_np(image)

    # TODO: Run inference on the processed image

    # TODO: Replace this demo dict with the result of the prediction
    return {"file_size": len(image)}
