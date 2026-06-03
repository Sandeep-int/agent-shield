import os
import uvicorn
from api.banner import print_banner

print_banner()

from api.main import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host="127.0.0.1", port=8000)