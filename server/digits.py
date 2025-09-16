#run    uvicorn digits:app --host 0.0.0.0 --port 8080 --reload

from io import BytesIO
from fastapi import FastAPI, File
from fastapi.responses import HTMLResponse
from typing import Annotated
from pathlib import Path
from pydantic import BaseModel

# Create the FastAPI app
app: FastAPI = FastAPI()

@app.get("/", response_class=HTMLResponse)
def get_main():
    html_path = Path("visuals.html")
    return html_path.read_text()

class ColorPayload(BaseModel):
    color: str

@app.post("/log_color")
def log_color(payload: ColorPayload):
    print(f"Client is viewing color: {payload.color}")
    return {"status": "color received"}