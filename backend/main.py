from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List
from datetime import datetime
import shutil, os, json, zipfile
import pdfplumber

app = FastAPI()

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lecture-sorter-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 파일 업로드 API
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

    for file in files:
        filename = file.filename
        extracted_text = ""

        # PDF 요약
        if filename.endswith(".pdf"):
            try:
                with pdfplumber.open(file.file) as pdf:
                    for page in pdf.pages[:3]:
                        extracted_text += page.extract_text() or ""
            except Exception as e:
                extracted_text = f"[PDF 열기 실패] {e}"

        extracted_text = extracted_text.strip().replace("\n", " ")
        if len(extracted_text) > 500:
            extracted_text = extracted_text[:500] + "..."

        # 저장 경로 생성
        base_path = f"./uploads/{upload_id}/{subject}/week_{week}"
        os.makedirs(base_path, exist_ok=True)

        # 파일 저장
        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        # 요약 저장
        summary_path = os.path.join(base_path, f"{os.path.splitext(filename)[0]}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(extracted_text or "내용 없음")

        results.append({
            "original_name": filename,
            "subject": subject,
            "week": week,
            "path": file_path,
            "summary": extracted_text,
        })

    return {"upload_id": upload_id, "results": results}

# 🔹 과제 등록 API
@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    assignment = {
        "upload_id": upload_id.strip(),
        "subject": subject.strip(),
        "title": title.strip(),
        "deadline": deadline.strip()
    }

    base_dir = f"./uploads/{upload_id}"
    os.makedirs(base_dir, exist_ok=True)

    path = os.path.join(base_dir, "assignments.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(assignment)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "과제가 저장되었습니다."}

# 🔹 업로드된 파일 목록 확인
@app.get("/uploads/{upload_id}")
async def get_uploaded_files(upload_id: str):
    base_path = f"./uploads/{upload_id}"
    if not os.path.exists(base_path):
        return JSONResponse(status_code=404, content={"message": "업로드된 파일이 없습니다."})

    result = {}
    for subject in os.listdir(base_path):
        subject_path = os.path.join(base_path, subject)
        if not os.path.isdir(subject_path):
            continue
        result[subject] = {}
        for week_folder in os.listdir(subject_path):
            week_path = os.path.join(subject_path, week_folder)
            files = [f for f in os.listdir(week_path) if not f.endswith("_summary.txt")]
            result[subject][week_folder] = files
    return result

# 🔹 과제 목록 확인
@app.get("/assignments/{upload_id}")
async def get_assignments(upload_id: str):
    path = f"./uploads/{upload_id}/assignments.json"
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"message": "과제 정보 없음"})
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# 🔹 zip 다운로드
@app.get("/zip/{upload_id}")
async def download_zip(upload_id: str):
    base_path = f"./uploads/{upload_id}"
    if not os.path.exists(base_path):
        return JSONResponse(status_code=404, content={"message": "업로드된 자료 없음"})

    zip_path = f"./uploads/{upload_id}_all.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, start=base_path)
                zipf.write(full_path, arcname=rel_path)

    return FileResponse(zip_path, filename=f"{upload_id}_자료.zip", media_type="application/zip")
