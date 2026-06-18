"""``python -m webapp`` 로 웹 서버를 실행한다.

환경변수 ``HOST``(기본 127.0.0.1), ``PORT``(기본 8000) 로 바인딩을 조절한다.
"""

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"\n  ▶ sound 웹 UI: http://{host}:{port}\n")
    uvicorn.run("webapp.server:app", host=host, port=port)
