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

        # 저장 경로: uploads/{upload_id}/{subject}/week_{week}/
        base_path = f"./uploads/{upload_id}/{subject}/week_{week}"
        os.makedirs(base_path, exist_ok=True)

        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        # 요약 텍스트 저장
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

    return {
        "upload_id": upload_id,
        "results": results
    }


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

    path = f"./uploads/{upload_id}/assignments.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(assignment)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "과제가 저장되었습니다."}
