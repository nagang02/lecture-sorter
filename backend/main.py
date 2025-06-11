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

# -----------------------------------
# 1) 기본 설정
# -----------------------------------
app = FastAPI(
    title="Lecture Sorter Backend",
    description="강의 자료 업로드·조회 및 과제 등록 기능 + ZIP 다운로드 기능을 제공하는 백엔드 API",
    version="1.0.0"
)

# CORS 허용 설정 (모든 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 운영 시에는 프론트엔드 도메인만 허용하도록 변경 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드한 파일을 저장할 최상위 디렉터리
UPLOAD_ROOT = "./uploads"

# 서버 시작 시, UPLOAD_ROOT 디렉터리가 없으면 생성
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT, exist_ok=True)

# -----------------------------------
# 1-1) 정적 파일(업로드된 PDF/요약 TXT 등)을 제공할 엔드포인트를 /files 로 마운트
# -----------------------------------
# 예: GET /files/{upload_id}/{subject}/week_{n}/lecture.pdf
app.mount("/files", StaticFiles(directory=UPLOAD_ROOT), name="files")


# -----------------------------------
# 2) /upload 엔드포인트: 파일 업로드 + 요약 생성
# -----------------------------------
@app.post("/upload")
async def upload_files(
    upload_id: str = Form(...),
    subject: str = Form(...),
    week: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    - upload_id: 사용자가 지정하는 고유 ID (예: "nagang")
    - subject: 과목명 (예: "디지털공학")
    - week: 주차 (예: "1", "2" 등)
    - files: 실제 업로드된 파일 리스트
    """
    upload_id = upload_id.strip()
    subject = subject.strip()
    week = week.strip()

    # 필수값 체크
    if not upload_id or not subject or not week or len(files) == 0:
        raise HTTPException(status_code=400, detail="upload_id, subject, week, files 모두 필요합니다.")

    results = []
    # 업로드 경로: ./uploads/{upload_id}/{subject}/week_{week}/
    base_path = os.path.join(UPLOAD_ROOT, upload_id, subject, f"week_{week}")
    os.makedirs(base_path, exist_ok=True)

    for file in files:
        filename = file.filename
        extracted_text = ""

        # PDF라면 첫 3페이지만 간단히 추출해서 '요약'으로 저장
        if filename.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(file.file) as pdf:
                    for page in pdf.pages[:3]:
                        page_text = page.extract_text() or ""
                        extracted_text += page_text + "\n"
            except Exception as e:
                extracted_text = f"[PDF 파싱 실패] {e}"

        # 간단히 텍스트 정리
        extracted_text = extracted_text.strip().replace("\r\n", "\n")
        if len(extracted_text) > 500:
            extracted_text = extracted_text[:500] + "..."

        # 실제 파일 저장
        file_path = os.path.join(base_path, filename)
        file.file.seek(0)
        with open(file_path, "wb") as out_f:
            shutil.copyfileobj(file.file, out_f)

        # 요약 텍스트를 별도 .txt 파일로 저장
        summary_filename = f"{os.path.splitext(filename)[0]}_summary.txt"
        summary_path = os.path.join(base_path, summary_filename)
        with open(summary_path, "w", encoding="utf-8") as txt_f:
            txt_f.write(extracted_text or "내용 없음")

        # 응답용 결과 항목에 추가
        results.append({
            "original_name": filename,
            "subject": subject,
            "week": week,
            # 실제 파일 접근 URL은 /files 라는 prefix를 통해 내려받는다
            "file_url": f"/files/{upload_id}/{subject}/week_{week}/{filename}",
            "summary_url": f"/files/{upload_id}/{subject}/week_{week}/{summary_filename}",
        })

    return {"upload_id": upload_id, "results": results}


# -----------------------------------
# 3) /assignments 엔드포인트: 과제 등록
# -----------------------------------
@app.post("/assignments")
async def register_assignment(
    upload_id: str = Form(...),
    subject: str = Form(...),
    title: str = Form(...),
    deadline: str = Form(...)
):
    """
    - upload_id: 업로드 ID (관련 자료 보여줄 디렉터리와 연동)
    - subject: 과목명
    - title: 과제 제목
    - deadline: 과제 제출 기한 ("YYYY-MM-DD" 형식)
    """
    upload_id = upload_id.strip()
    subject = subject.strip()
    title = title.strip()
    deadline = deadline.strip()

    if not upload_id or not subject or not title or not deadline:
        raise HTTPException(status_code=400, detail="모든 항목(upload_id, subject, title, deadline)이 필요합니다.")

    # 과제 저장 경로: ./uploads/{upload_id}/assignments.json
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


# -----------------------------------
# 4) /uploads/{upload_id} 엔드포인트: 업로드된 자료 조회 (JSON)
# -----------------------------------
@app.get("/uploads/{upload_id}")
async def get_upload_info(upload_id: str):
    """
    업로드된 자료(폴더 구조)를 JSON 형태로 반환합니다.
    {
      "과목1": {
        "1": ["lecture.pdf", "lecture_summary.txt", …],
        "2": [ … ],
      },
      "과목2": { … },
      "assignments": [ {subject, title, deadline}, … ]   # 있을 경우 과제 목록
    }
    """
    upload_id = upload_id.strip()
    target_dir = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    result = {}
    # 1) 과목별 week 디렉터리 순회
    for entry in os.listdir(target_dir):
        subject_path = os.path.join(target_dir, entry)
        if not os.path.isdir(subject_path):
            continue

        # "assignments.json" 파일은 따로 처리
        if entry == "assignments.json":
            continue

        subject_data = {}
        for week_folder in os.listdir(subject_path):
            week_path = os.path.join(subject_path, week_folder)
            if not os.path.isdir(week_path):
                continue

            # week_{n} 폴더 안의 파일 목록만 추출 (파일명만)
            file_list = [
                fname
                for fname in os.listdir(week_path)
                if os.path.isfile(os.path.join(week_path, fname))
            ]
            # 키는 “주차”만 남겨둔다 (week_ 를 제거)
            subject_data[week_folder.replace("week_", "")] = file_list

        if subject_data:
            result[entry] = subject_data

    # 2) assignments.json 파일이 있다면 과제 목록으로 추가
    assignment_path = os.path.join(target_dir, "assignments.json")
    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                assignments = json.load(f)
        except json.JSONDecodeError:
            assignments = []
        result["assignments"] = assignments

    return JSONResponse(result)


# -----------------------------------
# 5) /download/{upload_id} 엔드포인트: 전체 폴더를 ZIP으로 묶어 내려줌
# -----------------------------------
@app.get("/download/{upload_id}")
async def download_zip(upload_id: str):
    """
    upload_id 디렉터리 전체를 ZIP으로 압축하여 스트리밍 응답으로 내려줍니다.
    """
    upload_id = upload_id.strip()
    target_dir = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    # 메모리 상에서 ZIP 생성
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # target_dir 하위 모든 파일을 순회하며 ZIP에 추가
        for root, _, files in os.walk(target_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                # ZIP 안에 들어갈 경로를 상대경로로 계산
                rel_path = os.path.relpath(file_path, UPLOAD_ROOT)
                zf.write(file_path, arcname=rel_path)
    buf.seek(0)

    headers = {
        "Content-Disposition": f"attachment; filename={upload_id}.zip"
    }
    return StreamingResponse(buf, media_type="application/zip", headers=headers)


# -----------------------------------
# 6) 루트 요청 시 안내 메시지 (선택 사항)
# -----------------------------------
@app.get("/")
async def root():
    return {"message": "Lecture Sorter Backend가 정상 동작 중입니다. /docs 에서 Swagger UI를 확인하세요."}
