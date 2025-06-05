# backend/main.py

import os
import shutil
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber

app = FastAPI(
    title="Lecture Sorter Backend",
    description="강의 자료 업로드·조회 및 과제 등록 기능을 제공하는 백엔드 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 운영 시에는 프론트엔드 도메인만 허용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT = "./uploads"
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT, exist_ok=True)

# 업로드된 파일·요약을 정적 서빙
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")


@app.post("/upload")
async def upload_files(
    upload_id: str = Form(...),
    subject: str = Form(...),
    week: str = Form(...),
    files: List[UploadFile] = File(...)
):
    upload_id = upload_id.strip()
    subject = subject.strip()
    week = week.strip()

    if not upload_id or not subject or not week or len(files) == 0:
        raise HTTPException(status_code=400, detail="upload_id, subject, week, files 모두 필요합니다.")

    base_path = os.path.join(UPLOAD_ROOT, upload_id, subject, f"week_{week}")
    os.makedirs(base_path, exist_ok=True)

    results = []
    for file in files:
        filename = file.filename
        extracted_text = ""

        if filename.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(file.file) as pdf:
                    for page in pdf.pages[:3]:
                        extracted_text += (page.extract_text() or "") + "\n"
            except Exception as e:
                extracted_text = f"[PDF 파싱 실패] {e}"

        extracted_text = extracted_text.strip().replace("\r\n", "\n")
        if len(extracted_text) > 500:
            extracted_text = extracted_text[:500] + "..."

        # 실제 파일 저장
        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_f:
            shutil.copyfileobj(file.file, out_f)

        # 요약 텍스트 저장
        summary_filename = f"{os.path.splitext(filename)[0]}_summary.txt"
        summary_path = os.path.join(base_path, summary_filename)
        with open(summary_path, "w", encoding="utf-8") as txt_f:
            txt_f.write(extracted_text or "내용 없음")

        results.append({
            "original_name": filename,
            "subject": subject,
            "week": week,
            "file_url": f"/uploads/{upload_id}/{subject}/week_{week}/{filename}",
            "summary_url": f"/uploads/{upload_id}/{subject}/week_{week}/{summary_filename}",
        })

    return {"upload_id": upload_id, "results": results}


@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    upload_id = upload_id.strip()
    subject = subject.strip()
    title = title.strip()
    deadline = deadline.strip()

    if not upload_id or not subject or not title or not deadline:
        raise HTTPException(status_code=400, detail="모든 항목(upload_id, subject, title, deadline)이 필요합니다.")

    assignment_dir = os.path.join(UPLOAD_ROOT, upload_id)
    os.makedirs(assignment_dir, exist_ok=True)
    assignment_path = os.path.join(assignment_dir, "assignments.json")

    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    new_assignment = {
        "subject": subject,
        "title": title,
        "deadline": deadline
    }
    existing_data.append(new_assignment)

    with open(assignment_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    return {"message": "과제가 정상적으로 등록되었습니다."}


@app.get("/uploads/{upload_id}")
async def get_upload_info(upload_id: str):
    upload_id = upload_id.strip()
    target_dir = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    result = {}
    # 과목별 week 디렉터리 순회
    for subject_name in os.listdir(target_dir):
        subject_path = os.path.join(target_dir, subject_name)
        if not os.path.isdir(subject_path):
            continue
        if subject_name == "assignments.json":
            continue

        subject_data = {}
        for week_folder in os.listdir(subject_path):
            week_path = os.path.join(subject_path, week_folder)
            if not os.path.isdir(week_path):
                continue
            file_list = [
                fname
                for fname in os.listdir(week_path)
                if os.path.isfile(os.path.join(week_path, fname))
              ]
            subject_data[week_folder.replace("week_", "")] = file_list

        if subject_data:
            result[subject_name] = subject_data

    # assignments.json이 있으면 추가
    assignment_path = os.path.join(target_dir, "assignments.json")
    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                assignments = json.load(f)
        except json.JSONDecodeError:
            assignments = []
        result["assignments"] = assignments

    return JSONResponse(result)


@app.get("/")
async def root():
    return {"message": "Lecture Sorter Backend가 정상 동작 중입니다. /docs 확인하세요."}
