from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import shutil, os, json
import pdfplumber

app = FastAPI()

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔽 파일 업로드 API
@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    upload_id: str = Form(...),
    subject: str = Form(...),
    week: str = Form(...)
):
    upload_id = upload_id.strip()
    subject = subject.strip()
    week = week.strip()
    results = []

    base_path = f"./uploads/{upload_id}/{subject}/week_{week}"
    os.makedirs(base_path, exist_ok=True)

    for file in files:
        filename = file.filename
        extracted_text = ""

        # PDF 요약 처리
        if filename.endswith(".pdf"):
            try:
                with pdfplumber.open(file.file) as pdf:
                    for page in pdf.pages[:3]:
                        extracted_text += page.extract_text() or ""
            except Exception as e:
                extracted_text = f"[PDF 열기 실패] {e}"

        # 요약 정제
        extracted_text = extracted_text.strip().replace("\n", " ")
        if len(extracted_text) > 500:
            extracted_text = extracted_text[:500] + "..."

        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        # 요약 텍스트 저장
        summary_path = os.path.join(base_path, f"{os.path.splitext(filename)[0]}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(extracted_text or "내용 없음")

        results.append({
            "filename": filename,
            "summary": extracted_text,
            "saved_path": file_path
        })

    return {
        "upload_id": upload_id,
        "subject": subject,
        "week": week,
        "results": results
    }

# 🔽 과제 등록 API
@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    upload_id = upload_id.strip()
    subject = subject.strip()

    # uploads/{upload_id}/ 디렉토리 존재 보장
    base_path = f"./uploads/{upload_id}"
    os.makedirs(base_path, exist_ok=True)

    assignment = {
        "title": title.strip(),
        "deadline": deadline.strip(),
        "subject": subject
    }

    path = os.path.join(base_path, "assignments.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(assignment)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "과제가 저장되었습니다.", "assignment": assignment}

# 🔽 업로드된 파일 목록 보기
@app.get("/list_files")
async def list_files(upload_id: str):
    base_path = f"./uploads/{upload_id}"
    file_info = []

    if not os.path.exists(base_path):
        return {"message": "업로드 기록 없음", "files": []}

    for subject in os.listdir(base_path):
        subject_path = os.path.join(base_path, subject)
        if os.path.isdir(subject_path):
            for week_folder in os.listdir(subject_path):
                week_path = os.path.join(subject_path, week_folder)
                files = os.listdir(week_path)
                file_info.append({
                    "subject": subject,
                    "week": week_folder,
                    "files": files
                })

    return {"upload_id": upload_id, "files": file_info}

# 🔽 과제 목록 보기
@app.get("/list_assignments")
async def list_assignments(upload_id: str):
    path = f"./uploads/{upload_id}/assignments.json"
    if not os.path.exists(path):
        return {"message": "과제 기록 없음", "assignments": []}
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return {"upload_id": upload_id, "assignments": data}
