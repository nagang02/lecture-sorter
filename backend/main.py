# backend/main.py

import os
import shutil
import json
import io
import zipfile
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
from urllib.parse import quote

# -----------------------------------
# 1) 기본 설정
# -----------------------------------
app = FastAPI(
    title="Lecture Sorter Backend",
    description="강의 자료 업로드·조회, 과제 등록, 파일 삭제 및 ZIP 다운로드 기능을 제공하는 백엔드 API",
    version="1.1.0"
)

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드 파일을 저장할 최상위 디렉터리
UPLOAD_ROOT = "./uploads"

# 서버 시작 시, UPLOAD_ROOT 디렉터리가 없으면 생성
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT, exist_ok=True)

# -----------------------------------
# 2) 정적 파일 제공 설정
# -----------------------------------
app.mount("/files", StaticFiles(directory=UPLOAD_ROOT), name="files")

# -----------------------------------
# 3) /upload 엔드포인트: 파일 업로드
# -----------------------------------
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

    if not all([upload_id, subject, week]) or not files:
        raise HTTPException(status_code=400, detail="모든 필드를 채워주세요.")

    base_path = os.path.join(UPLOAD_ROOT, upload_id, subject, f"week_{week}")
    os.makedirs(base_path, exist_ok=True)

    results = []
    for file in files:
        filename = file.filename
        file_path = os.path.join(base_path, filename)

        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # PDF 요약 처리
        if filename.lower().endswith(".pdf"):
            summary_filename = f"{os.path.splitext(filename)[0]}_summary.txt"
            summary_path = os.path.join(base_path, summary_filename)
            extracted_text = ""
            try:
                # 파일 포인터를 처음으로 되돌림
                file.file.seek(0)
                with pdfplumber.open(file.file) as pdf:
                    for page in pdf.pages[:3]: #
                        page_text = page.extract_text() or ""
                        extracted_text += page_text + "\n"
                
                with open(summary_path, "w", encoding="utf-8") as txt_f:
                    txt_f.write(extracted_text.strip()[:500] + "...")
            except Exception as e:
                print(f"PDF 처리 실패: {e}")


        results.append({"original_name": filename})

    return {"upload_id": upload_id, "results": results}

# -----------------------------------
# 4) /assignments 엔드포인트: 과제 등록
# -----------------------------------
@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    upload_id = upload_id.strip()
    if not all([upload_id, subject, title, deadline]):
        raise HTTPException(status_code=400, detail="모든 항목이 필요합니다.")

    assignment_dir = os.path.join(UPLOAD_ROOT, upload_id)
    os.makedirs(assignment_dir, exist_ok=True)
    assignment_path = os.path.join(assignment_dir, "assignments.json")

    existing_data = []
    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass

    new_assignment = {"subject": subject, "title": title, "deadline": deadline}
    existing_data.append(new_assignment)

    with open(assignment_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    return {"message": "과제가 정상적으로 등록되었습니다."}

# -----------------------------------
# 5) /uploads/{upload_id} 엔드포인트: 업로드된 자료 조회
# -----------------------------------
@app.get("/uploads/{upload_id}")
async def get_upload_info(upload_id: str):
    target_dir = os.path.join(UPLOAD_ROOT, upload_id.strip())
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    result = {}
    for subject_name in os.listdir(target_dir):
        subject_path = os.path.join(target_dir, subject_name)
        if os.path.isdir(subject_path):
            subject_data = {}
            for week_folder in os.listdir(subject_path):
                week_path = os.path.join(subject_path, week_folder)
                if os.path.isdir(week_path) and week_folder.startswith("week_"):
                    files = [f for f in os.listdir(week_path) if os.path.isfile(os.path.join(week_path, f))]
                    week_num = week_folder.replace("week_", "")
                    subject_data[week_num] = sorted(files)
            if subject_data:
                result[subject_name] = subject_data

    assignment_path = os.path.join(target_dir, "assignments.json")
    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                result["assignments"] = json.load(f)
        except json.JSONDecodeError:
            pass

    return JSONResponse(result)

# -----------------------------------
# 6) /download/{upload_id} 엔드포인트: 전체 폴더 ZIP 다운로드
# -----------------------------------
@app.get("/download/{upload_id}")
async def download_zip(upload_id: str):
    target_dir = os.path.join(UPLOAD_ROOT, upload_id.strip())
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(target_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, UPLOAD_ROOT)
                zf.write(file_path, arcname=rel_path)
    buf.seek(0)

    filename_encoded = quote(f"{upload_id}.zip")
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
    }
    return StreamingResponse(buf, media_type="application/zip", headers=headers)

# -----------------------------------
# 7) /delete-file 엔드포인트: 특정 파일 삭제
# -----------------------------------
@app.post("/delete-file")
async def delete_file(
    upload_id: str = Form(...),
    subject: str = Form(...),
    week: str = Form(...),
    file_name: str = Form(...)
):
    try:
        base_path = os.path.join(UPLOAD_ROOT, upload_id, subject, f"week_{week}")
        file_path = os.path.join(base_path, file_name)

        summary_filename = f"{os.path.splitext(file_name)[0]}_summary.txt"
        summary_path = os.path.join(base_path, summary_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise HTTPException(status_code=404, detail=f"{file_name} 파일을 찾을 수 없습니다.")

        if os.path.exists(summary_path):
            os.remove(summary_path)

        return {"message": "파일이 성공적으로 삭제되었습니다.", "deleted_file": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------
# 8) 루트 엔드포인트: 서버 상태 확인
# -----------------------------------
@app.get("/")
async def root():
    return {"message": "Lecture Sorter Backend가 정상 동작 중입니다."}
