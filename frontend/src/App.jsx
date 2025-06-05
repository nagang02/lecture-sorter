import React, { useState } from "react";
import axios from "axios";
import QRCode from "qrcode.react";

function App() {
  const [uploadId, setUploadId] = useState("");
  const [subject, setSubject] = useState("");
  const [week, setWeek] = useState("");
  const [files, setFiles] = useState([]);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentDeadline, setAssignmentDeadline] = useState("");
  const [uploadResult, setUploadResult] = useState(null);

  const handleUpload = async () => {
    if (!uploadId || !subject || !week || files.length === 0) {
      alert("모든 항목을 입력하고 파일을 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("week", week);
    for (const file of files) {
      formData.append("files", file);
    }

    try {
      const response = await axios.post(
        "https://lecture-sorter-backend.onrender.com/upload",
        formData
      );
      setUploadResult(response.data);
      alert("업로드 성공!");
    } catch (error) {
      console.error(error);
      alert("업로드 실패");
    }
  };

  const handleRegisterAssignment = async () => {
    if (!uploadId || !subject || !assignmentTitle || !assignmentDeadline) {
      alert("모든 항목을 입력해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("title", assignmentTitle);
    formData.append("deadline", assignmentDeadline);

    try {
      await axios.post(
        "https://lecture-sorter-backend.onrender.com/assignments",
        formData
      );
      alert("과제 등록 성공!");
    } catch (error) {
      console.error(error);
      alert("과제 등록 실패");
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20, fontFamily: "sans-serif" }}>
      <h1>📚 Lecture Sorter</h1>

      <label>Upload ID:</label>
      <input
        type="text"
        value={uploadId}
        onChange={(e) => setUploadId(e.target.value)}
        placeholder="예: nagang"
        style={{ width: "100%", marginBottom: 10 }}
      />

      <label>Subject:</label>
      <input
        type="text"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        placeholder="예: 디지털공학"
        style={{ width: "100%", marginBottom: 10 }}
      />

      <label>Week:</label>
      <input
        type="text"
        value={week}
        onChange={(e) => setWeek(e.target.value)}
        placeholder="예: 10"
        style={{ width: "100%", marginBottom: 10 }}
      />

      <label>Files:</label>
      <input
        type="file"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files))}
        style={{ width: "100%", marginBottom: 20 }}
      />

      <button onClick={handleUpload} style={{ marginBottom: 30 }}>📤 업로드</button>

      <hr />

      <h2>📝 과제 등록</h2>
      <label>과제 제목:</label>
      <input
        type="text"
        value={assignmentTitle}
        onChange={(e) => setAssignmentTitle(e.target.value)}
        placeholder="예: 기말 프로젝트"
        style={{ width: "100%", marginBottom: 10 }}
      />

      <label>제출 기한:</label>
      <input
        type="date"
        value={assignmentDeadline}
        onChange={(e) => setAssignmentDeadline(e.target.value)}
        style={{ width: "100%", marginBottom: 20 }}
      />

      <button onClick={handleRegisterAssignment} style={{ marginBottom: 30 }}>✅ 과제 등록</button>

      {uploadId && (
        <div style={{ marginTop: "40px", borderTop: "1px solid #ccc", paddingTop: "30px" }}>
          <h3>📦 업로드 완료!</h3>
          <p>아래 링크로 언제든지 접속하여 확인할 수 있어요:</p>
          <a
            href={`https://lecture-sorter-frontend.onrender.com/uploads/${uploadId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ wordBreak: "break-all", color: "blue" }}
          >
            https://lecture-sorter-frontend.onrender.com/uploads/{uploadId}
          </a>

          <h4 style={{ marginTop: "20px" }}>📱 QR코드로 공유</h4>
          <QRCode
            value={`https://lecture-sorter-frontend.onrender.com/uploads/${uploadId}`}
            size={160}
            includeMargin={true}
          />

          <p style={{ marginTop: "10px", color: "#888" }}>
            이 QR을 스캔하거나 링크를 즐겨찾기 해두면 편리해요!
          </p>
        </div>
      )}
    </div>
  );
}

export default App;
