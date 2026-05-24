
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import app as agent_app

api = FastAPI()
api.mount("/static", StaticFiles(directory="static"), name="static")

class AnalyzeRequest(BaseModel):
    company: str = ""
    email_content: str = ""

@api.get("/")
def root():
    return FileResponse("static/index.html")

@api.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = agent_app.invoke({
        "company": request.company,
        "email_content": request.email_content,
        "search_results": "",
        "red_flags": "",
        "scam_score": 0,
        "summary": ""
    })
    return {
        "scam_score": result["scam_score"],
        "red_flags": result["red_flags"],
        "summary": result["summary"],
        "company": result["company"]
    }