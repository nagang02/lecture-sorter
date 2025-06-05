from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import shutil, os, json
import pdfplumber
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import zipfile



# ✅ uploads 폴더 없으면 생성
UPLOAD_ROOT = './uploads'
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT = "./uploads"
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    upload_id: str = Form(...),
    subject: str = Form(...),
    week: str = Form(...)
):
    upload_id, subject, week = upload_id.strip(), subject.strip(), week.strip()
    results = []

    for file in files:
        filename = file.filename
        extracted_text = ""

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

        base_path = os.path.join(UPLOAD_ROOT, upload_id, subject, f"week_{week}")
        os.makedirs(base_path, exist_ok=True)

        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_file:
            shutil.copyfileobj(file.file, out_file)

        summary_path = os.path.join(base_path, f"{os.path.splitext(filename)[0]}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(extracted_text or "내용 없음")

        results.append({
            "original_name": filename,
            "subject": subject,
            "week": week,
            "path": file_path,
            "summary": extracted_text
        })

    return {"upload_id": upload_id, "results": results}

@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    path = os.path.join(UPLOAD_ROOT, upload_id, "assignments.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    assignment = {
        "subject": subject.strip(),
        "title": title.strip(),
        "deadline": deadline.strip()
    }

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(assignment)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "과제가 저장되었습니다."}

@app.get("/uploads/{upload_id}")
async def get_upload_contents(upload_id: str):
    upload_dir = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(upload_dir):
        return JSONResponse(status_code=404, content={"error": "해당 ID의 업로드 내용이 존재하지 않습니다."})

    result = {"files": [], "assignments": []}

    for root, dirs, files in os.walk(upload_dir):
        for file in files:
            if file.endswith("_summary.txt"):
                continue  # 요약 파일은 따로 보여주지 않음
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, upload_dir)
            result["files"].append(rel_path)

    assignment_path = os.path.join(upload_dir, "assignments.json")
    if os.path.exists(assignment_path):
        with open(assignment_path, "r", encoding="utf-8") as f:
            result["assignments"] = json.load(f)

    return result

@app.get("/zip/{upload_id}")
async def download_zip(upload_id: str):
    upload_path = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(upload_path):
        return JSONResponse(status_code=404, content={"error": "업로드 ID가 존재하지 않습니다."})

    zip_path = f"/tmp/{upload_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(upload_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, upload_path)
                zipf.write(full_path, arcname=rel_path)

    return FileResponse(zip_path, filename=f"{upload_id}.zip", media_type="application/zip")
