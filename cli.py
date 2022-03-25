import uvicorn

from main import app


if __name__ == '__main__':
    uvicorn.run(app, port=8000, log_level="debug")
