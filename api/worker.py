from uvicorn.workers import UvicornWorker

class Worker(UvicornWorker):
    CONFIG_KWARGS = {
        "root_path": "/api/v1"
    }
