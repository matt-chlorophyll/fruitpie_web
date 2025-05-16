from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

class JobPost(BaseModel):
    posted_date: date
    status: str
    title: str
    company: str
    description: str
    requirements: str
    location: str
    salary: Optional[str] = None
    contact: str
    notes: Optional[str] = None

# Sample Data (we'll replace this later, perhaps with Excel import)
sample_jobs = [
    JobPost(
        posted_date=date(2023, 10, 26),
        status="Hiring",
        title="Software Engineer",
        company="FruitPie Tech",
        description="Developing the core fruit sorting algorithms.",
        requirements="Python, FastAPI, 3+ years experience",
        location="Apple Valley, CA",
        salary="$100,000 - $120,000",
        contact="hr@fruitpietech.com",
        notes="Great team, lots of free fruit!"
    ),
    JobPost(
        posted_date=date(2023, 11, 5),
        status="Hiring",
        title="UX Designer",
        company="OrangeBloom Inc.",
        description="Designing intuitive interfaces for our citrus marketplace.",
        requirements="Figma, Adobe XD, User Research",
        location="Orange County, FL",
        salary="$90,000 - $110,000",
        contact="careers@orangebloom.com",
        notes="Sunny office environment."
    ),
    JobPost(
        posted_date=date(2023, 11, 15),
        status="Closed",
        title="Data Analyst",
        company="BerryMetrics Co.",
        description="Analyzing sales data for berry-based products.",
        requirements="SQL, Python, Tableau",
        location="Remote (US)",
        contact="jobs@berrymetrics.com",
        notes="Position filled quickly."
    )
]

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "jobs": sample_jobs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 