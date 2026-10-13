from waitress import serve
from backend_mysql import app


if __name__ == "__main__":
    print("启动地址：http://127.0.0.1:8000")

    serve(
        app,
        host="127.0.0.1",
        port=8000,
        threads=4,
    )