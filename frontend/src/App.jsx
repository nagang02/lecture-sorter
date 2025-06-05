import React, { useState } from "react";
import axios from "axios";

function App() {
  const [uploadId, setUploadId] = useState("");
  const [files, setFiles] = useState([]);
  const [subject, setSubject] = useState("디지털공학");
  const [customSubject, setCustomSubject] = useState("");
  const [week, setWeek] = useState("1");
  const [results, setResults] = useState([]);
  const [showSummary, setShowSummary] = useState(null);
  const [assignment, setAssignment] = useState({
    subject: "디지털공학",
    title: "",
    deadline: ""
  });

  const subjectOptions = [
    "디지털공학",
    "전응실",
    "전자회로",
    "신호및시스템",
    "직접 입력"
  ];

  const weekOptions = Array.from({ length: 15 }, (_, i) => `${i + 1}`);
  const backendUrl = import.meta.env.VITE_BACKEND_URL;

  const handleUpload = async () => {
    if (!uploadId.trim()) {
      alert("고유 ID를 입력하세요!");
      return;
    }

    const finalSubject = subject === "직접 입력" ? customSubject.trim() : subject;
    if (!finalSubject) return alert("과목명을 입력하세요!");

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("upload_id", uploadId);
    formData.append("subject", finalSubject);
    formData.append("week", week);

    try {
      const res = await axios.post(`${backendUrl}/upload`, formData);
      setResults(res.data.results);
    } catch (error) {
      alert("업로드 중 오류가 발생했습니다.");
      console.error(error);
    }
  };

  const handleAssignmentSubmit = async () => {
    if (!uploadId.trim()) {
      alert("고유 ID를 입력하세요!");
      return;
    }

    const finalSubject = assignment.subject === "직접 입력" ? customSubject.trim() : assignment.subject;
    if (!finalSubject || !assignment.title || !assignment.deadline) {
      alert("모든 항목을 입력하세요");
      return;
    }

    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", finalSubject);
    formData.append("title", assignment.title);
    formData.append("deadline", assignment.deadline);

    try {
      await axios.post(`${backendUrl}/assignments`, formData);
      alert("과제 등록 완료!");
      setAssignment({ subject: "디지털공학", title: "", deadline: "" });
    } catch (error) {
      alert("과제 등록 실패");
      console.error(error);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>📁 강의자료 자동 정리 시스템</h1>

      <label>🔑 고유 ID (폴더명 역할):</label>
      <input
        type="text"
        placeholder="예: yskim01"
        value={uploadId}
        onChange={(e) => setUploadId(e.target.value)}
        style={{ display: "block", marginBottom: "10px", padding: "5px" }}
      />

      <label>과목 선택:</label>
      <select
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        style={{ marginBottom: "10px", padding: "5px" }}
      >
        {subjectOptions.map((subj, idx) => (
          <option key={idx} value={subj}>{subj}</option>
        ))}
      </select>

      {subject === "직접 입력" && (
        <input
          type="text"
          placeholder="과목명 직접 입력"
          value={customSubject}
          onChange={(e) => setCustomSubject(e.target.value)}
          style={{ display: "block", marginBottom: "10px", padding: "5px" }}
        />
      )}

      <label>주차 선택:</label>
      <select
        value={week}
        onChange={(e) => setWeek(e.target.value)}
        style={{ marginBottom: "10px", padding: "5px" }}
      >
        {weekOptions.map((w, idx) => (
          <option key={idx} value={w}>{w}주차</option>
        ))}
      </select>

      <input
        type="file"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files))}
        style={{ marginBottom: "10px" }}
      />

      <button onClick={handleUpload}>📤 업로드</button>

      {results.map((file, idx) => (
        <div key={idx} style={{ border: "1px solid #ccc", marginTop: "20px", padding: "10px" }}>
          <p><strong>📎 파일명:</strong> {file.original_name}</p>
          <p><strong>📚 과목:</strong> {file.subject}</p>
          <p><strong>🗓️ 주차:</strong> {file.week}주차</p>
          <p><strong>📁 저장 위치:</strong> {file.path}</p>
          <button onClick={() => setShowSummary(file.summary)}>📄 요약 보기</button>
        </div>
      ))}

      {showSummary && (
        <div style={{
          position: "fixed",
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -30%)",
          backgroundColor: "#fff",
          padding: "20px",
          border: "1px solid #333",
          boxShadow: "0 0 10px rgba(0,0,0,0.3)",
          zIndex: 999
        }}>
          <h3>📄 요약 내용</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{showSummary}</p>
          <button onClick={() => setShowSummary(null)}>닫기</button>
        </div>
      )}

      <hr style={{ margin: "40px 0" }} />
      <h2>📝 과제 등록</h2>

      <select
        value={assignment.subject}
        onChange={(e) => setAssignment({ ...assignment, subject: e.target.value })}
        style={{ marginBottom: "10px", padding: "5px" }}
      >
        {subjectOptions.map((s, idx) => (
          <option key={idx} value={s}>{s}</option>
        ))}
      </select>

      {assignment.subject === "직접 입력" && (
        <input
          type="text"
          placeholder="과목명 직접 입력"
          value={customSubject}
          onChange={(e) => setCustomSubject(e.target.value)}
          style={{ display: "block", marginBottom: "10px", padding: "5px" }}
        />
      )}

      <input
        type="text"
        placeholder="과제 제목"
        value={assignment.title}
        onChange={(e) => setAssignment({ ...assignment, title: e.target.value })}
        style={{ display: "block", marginBottom: "10px", padding: "5px" }}
      />

      <input
        type="date"
        value={assignment.deadline}
        onChange={(e) => setAssignment({ ...assignment, deadline: e.target.value })}
        style={{ display: "block", marginBottom: "10px", padding: "5px" }}
      />

      <button onClick={handleAssignmentSubmit}>✅ 과제 등록</button>
    </div>
  );
}

export default App;
