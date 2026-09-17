import os
from dotenv import load_dotenv
load_dotenv()
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT","8000")), reload=False)
