// App.jsx
import React, { useState } from "react";
import axios from "axios";

function App() {
  const [uploadId, setUploadId] = useState("");
  const [subject, setSubject] = useState("");
  const [week, setWeek] = useState("1");
  const [files, setFiles] = useState([]);
  const [assignment, setAssignment] = useState({ subject: "", title: "", deadline: "" });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const backendUrl = import.meta.env.VITE_BACKEND_URL;

  const handleUpload = async () => {
    if (!uploadId || !subject || !week || files.length === 0) {
      alert("모든 항목을 입력하세요.");
      return;
    }

    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("week", week);

    try {
      await axios.post(`${backendUrl}/upload`, formData);
      alert("파일 업로드 성공!");
    } catch (err) {
      alert("업로드 실패");
      console.error(err);
    }
  };

  const handleAssignmentSubmit = async () => {
    const { subject, title, deadline } = assignment;
    if (!uploadId || !subject || !title || !deadline) {
      alert("모든 항목을 입력하세요.");
      return;
    }

    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("title", title);
    formData.append("deadline", deadline);

    try {
      await axios.post(`${backendUrl}/assignments`, formData);
      alert("과제 등록 성공!");
    } catch (err) {
      alert("과제 등록 실패");
      console.error(err);
    }
  };

  const handleFetchUploads = async () => {
    try {
      const res = await axios.get(`${backendUrl}/uploads/${uploadId}`);
      setUploadedFiles(res.data.files || []);
      setAssignments(res.data.assignments || []);
    } catch (err) {
      alert("업로드 내용을 불러오지 못했습니다.");
      console.error(err);
    }
  };

  const handleDownloadZip = () => {
    if (!uploadId) return alert("업로드 ID를 입력하세요.");
    window.open(`${backendUrl}/zip/${uploadId}`, "_blank");
  };

  return (
    <div style={{ padding: "30px" }}>
      <h1>📁 Lecture Sorter</h1>

      <input
        type="text"
        value={uploadId}
        onChange={(e) => setUploadId(e.target.value)}
        placeholder="업로드 ID (예: mynote123)"
        style={{ padding: "5px", width: "250px", marginBottom: "10px" }}
      />

      <div style={{ marginBottom: "10px" }}>
        <input
          type="text"
          placeholder="과목명"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          style={{ padding: "5px", marginRight: "10px" }}
        />
        <input
          type="text"
          placeholder="주차 (숫자)"
          value={week}
          onChange={(e) => setWeek(e.target.value)}
          style={{ padding: "5px", width: "60px" }}
        />
      </div>

      <input
        type="file"
        multiple
        onChange={(e) => setFiles([...e.target.files])}
        style={{ marginBottom: "10px" }}
      />
      <button onClick={handleUpload}>📤 파일 업로드</button>

      <hr style={{ margin: "30px 0" }} />

      <h2>📝 과제 등록</h2>
      <input
        type="text"
        placeholder="과목명"
        value={assignment.subject}
        onChange={(e) => setAssignment({ ...assignment, subject: e.target.value })}
        style={{ padding: "5px", marginRight: "10px" }}
      />
      <input
        type="text"
        placeholder="과제 제목"
        value={assignment.title}
        onChange={(e) => setAssignment({ ...assignment, title: e.target.value })}
        style={{ padding: "5px", marginRight: "10px" }}
      />
      <input
        type="date"
        value={assignment.deadline}
        onChange={(e) => setAssignment({ ...assignment, deadline: e.target.value })}
        style={{ padding: "5px", marginRight: "10px" }}
      />
      <button onClick={handleAssignmentSubmit}>✅ 과제 등록</button>

      <hr style={{ margin: "30px 0" }} />

      <h2>🔍 업로드 확인 및 다운로드</h2>
      <button onClick={handleFetchUploads} style={{ marginRight: "10px" }}>업로드 내용 보기</button>
      <button onClick={handleDownloadZip}>Zip 다운로드</button>

      <div style={{ marginTop: "20px" }}>
        <h3>📦 업로드된 파일 목록</h3>
        {uploadedFiles.length === 0 ? (
          <p>표시할 파일이 없습니다.</p>
        ) : (
          uploadedFiles.map((f, idx) => (
            <div key={idx} style={{ borderBottom: "1px solid #ddd", padding: "5px 0" }}>
              <strong>{f.filename}</strong> ({f.subject} / {f.week}주차)
              <br />
              요약: {f.summary}
            </div>
          ))
        )}
      </div>

      <div style={{ marginTop: "30px" }}>
        <h3>📝 등록된 과제</h3>
        {assignments.length === 0 ? (
          <p>등록된 과제가 없습니다.</p>
        ) : (
          assignments.map((a, idx) => (
            <div key={idx} style={{ borderBottom: "1px solid #ccc", padding: "5px 0" }}>
              <strong>{a.subject}</strong> - {a.title} (마감일: {a.deadline})
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default App;
