# send_email.py - 과제 마감 하루 전 이메일 알림 스크립트

import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# 📧 설정
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_ADDRESS = 'hope747044@gmail.com'         # 너의 Gmail 주소
EMAIL_PASSWORD = 'psgrhyhukeldjolh'            # 앱 비밀번호 (공백 없이!)
TARGET_EMAIL = 'hope747044@gmail.com'          # 받을 주소 (지금은 본인에게)

# ⏰ 오늘 날짜 기준으로 마감 하루 전 찾기
def get_due_assignments():
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    due_list = []

    try:
        with open('assignments.json', 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    except:
        return []

    for a in assignments:
        try:
            due_date = datetime.strptime(a['deadline'], '%Y-%m-%d')
            if due_date.date() == tomorrow.date():
                due_list.append(a)
        except:
            continue

    return due_list

# 📬 이메일 보내기
def send_email(assignments):
    if not assignments:
        print("✅ 오늘 마감 임박 과제 없음")
        return

    subject = "⏰ 내일 마감되는 과제가 있습니다!"
    body = "\n\n".join([
        f"📚 과목: {a['subject']}\n📝 제목: {a['title']}\n📅 마감일: {a['deadline']}"
        for a in assignments
    ])

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TARGET_EMAIL

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print("✅ 메일 전송 완료!")
    except Exception as e:
        print(f"❌ 메일 전송 실패: {e}")

if __name__ == "__main__":
    due_assignments = get_due_assignments()
    send_email(due_assignments)
