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

# -----------------------------------
# 1) 기본 설정
# -----------------------------------
app = FastAPI(
    title="Lecture Sorter Backend",
    description="강의 자료 업로드·조회 및 과제 등록 기능을 제공하는 백엔드 API",
    version="1.0.0"
)

# CORS 허용 설정 (모든 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 실제 운영 시에는 프론트엔드 도메인만 허용하도록 변경 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드한 파일을 저장할 최상위 디렉터리
UPLOAD_ROOT = "./uploads"

# 만약 디렉터리가 없으면 자동으로 생성해 둡니다.
# (서버가 시작될 때 한 번만 실행)
if not os.path.exists(UPLOAD_ROOT):
    os.makedirs(UPLOAD_ROOT, exist_ok=True)

# StaticFiles로 업로드된 파일을 브라우저에서 직접 볼 수 있도록 마운트
# 예: GET /uploads/{upload_id}/디지털공학/week_1/슬라이드.pdf
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")


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
    - upload_id: 사용자가 임의로 지정하는 고유 ID (예: "nagang")
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
            "file_url": f"/uploads/{upload_id}/{subject}/week_{week}/{filename}",
            "summary_url": f"/uploads/{upload_id}/{subject}/week_{week}/{summary_filename}",
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

    # 기존 파일이 있으면 읽어서 리스트로 불러오고, 없으면 빈 리스트
    if os.path.exists(assignment_path):
        try:
            with open(assignment_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    else:
        existing_data = []

    # 새 과제 항목 추가
    new_assignment = {
        "subject": subject,
        "title": title,
        "deadline": deadline
    }
    existing_data.append(new_assignment)

    # assignments.json에 덮어쓰기
    with open(assignment_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    return {"message": "과제가 정상적으로 등록되었습니다."}


# -----------------------------------
# 4) /uploads/{upload_id} 엔드포인트: 업로드된 자료 조회
# -----------------------------------
@app.get("/uploads/{upload_id}")
async def get_upload_info(upload_id: str):
    """
    업로드된 자료(폴더 구조)를 JSON 형태로 반환합니다.
    {
      "과목1": {
        "week_1": ["fileA.pdf", "fileB.pdf", "fileA_summary.txt", ...],
        "week_2": [ ... ]
      },
      "과목2": { ... },
      "assignments": [ {subject, title, deadline}, ... ]   # 있을 경우 과제 목록
    }
    """

    upload_id = upload_id.strip()
    target_dir = os.path.join(UPLOAD_ROOT, upload_id)
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="해당 upload_id의 자료를 찾을 수 없습니다.")

    result = {}
    # 1) 과목별 week 디렉터리 순회
    for subject_name in os.listdir(target_dir):
        subject_path = os.path.join(target_dir, subject_name)
        if not os.path.isdir(subject_path):
            continue

        # "assignments.json" 파일은 따로 처리
        if subject_name == "assignments.json":
            continue

        # subject_name이 과목 디렉터리라면 내부에 week_{n} 폴더들이 있을 것
        subject_data = {}
        for week_folder in os.listdir(subject_path):
            week_path = os.path.join(subject_path, week_folder)
            if not os.path.isdir(week_path):
                continue

            # week_{n} 폴더 안의 파일 목록만 추출 (파일명만)
            file_list = [fname for fname in os.listdir(week_path) if os.path.isfile(os.path.join(week_path, fname))]
            # 예: ["강의슬라이드.pdf", "강의슬라이드_summary.txt", ...]
            subject_data[week_folder.replace("week_", "")] = file_list

        if subject_data:
            result[subject_name] = subject_data

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
# 5) 루트 요청 시 안내 메시지 (선택 사항)
# -----------------------------------
@app.get("/")
async def root():
    return {"message": "Lecture Sorter Backend가 정상 동작 중입니다. /docs 에서 Swagger UI를 확인하세요."}
