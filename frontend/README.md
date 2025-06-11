# Lecture Sorter 실행 방법

이 프로젝트는 React로 제작된 프론트엔드와 Python(FastAPI)으로 제작된 백엔드로 구성되어 있습니다. 각 서버를 별도로 실행해야 합니다.

## 사전 요구사항

* Node.js (LTS 버전)
* Python (3.11 이상)

## 백엔드 실행 방법 (서버)

1.  새로운 터미널(명령 프롬프트)을 엽니다.
2.  백엔드 폴더로 이동합니다.
    ```shell
    cd backend
    ```
3.  필요한 라이브러리를 설치합니다.
    ```shell
    pip install -r requirements.txt
    ```
4.  백엔드 서버를 실행합니다.
    ```shell
    uvicorn main:app --reload
    ```
5.  서버는 `http://127.0.0.1:8000` 주소에서 실행됩니다. 이 터미널은 켜두세요.

## 프론트엔드 실행 방법 (사용자 화면)

1.  또 다른 새 터미널을 엽니다. (백엔드 터미널은 켜둔 채로)
2.  프론트엔드 폴더로 이동합니다.
    ```shell
    cd frontend
    ```
3.  필요한 라이브러리를 설치합니다. (시간이 조금 걸릴 수 있습니다)
    ```shell
    npm install
    ```
4.  프론트엔드 개발 서버를 실행합니다.
    ```shell
    npm run dev
    ```
5.  웹 브라우저에서 `http://localhost:5173` (또는 터미널에 나오는 주소)로 접속하여 웹사이트를 확인합니다.