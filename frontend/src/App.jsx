// frontend/src/App.jsx

import React, { useState, useEffect } from "react";
import {
  HashRouter as Router,
  Routes,
  Route,
  useParams
} from "react-router-dom";
import axios from "axios";
import { QRCodeCanvas } from "qrcode.react";

// ---------------------------------------------
// 1) 업로드 결과 보기 컴포넌트 (GET /uploads/{uploadId})
// ---------------------------------------------
function UploadViewer() {
  const { uploadId } = useParams();
  const [uploadedData, setUploadedData] = useState(null);

  useEffect(() => {
    axios
      .get(`https://lecture-sorter-backend.onrender.com/uploads/${uploadId}`)
      .then((res) => setUploadedData(res.data))
      .catch((err) => {
        console.error(err);
        setUploadedData({ error: true });
      });
  }, [uploadId]);

  if (!uploadedData) return <p>불러오는 중...</p>;
  if (uploadedData.error) return <p>업로드 정보를 불러오지 못했습니다.</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20, fontFamily: "sans-serif" }}>
      <h2>📂 업로드 ID: {uploadId}</h2>

      {/* 1) 과목별로 순회 */}
      {Object.entries(uploadedData).map(([subject, weeks]) => {
        // assignments 키는 넘어가지 않도록 분기
        if (subject === "assignments") return null;

        return (
          <div key={subject}>
            <h3>과목: {subject}</h3>
            {Object.entries(weeks).map(([week, files]) => (
              <div key={week} style={{ marginLeft: 20 }}>
                <h4>{week}주차</h4>
                <ul>
                  {files.map((fileName, idx) => (
                    <li key={idx}>
                      {/* 실제 파일 다운로드 경로는 /files/ 로 시작 */}
                      <a
                        href={`https://lecture-sorter-backend.onrender.com/files/${uploadId}/${subject}/week_${week}/${fileName}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {fileName}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        );
      })}

      {/* 2) assignments 목록이 있으면 보여주기 */}
      {uploadedData.assignments && (
        <div style={{ marginTop: 30, borderTop: "1px solid #ddd", paddingTop: 20 }}>
          <h3>📝 과제 목록</h3>
          <ul>
            {uploadedData.assignments.map((asgmt, idx) => (
              <li key={idx}>
                [{asgmt.subject}] {asgmt.title} – 기한: {asgmt.deadline}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 3) ZIP 다운로드 버튼 */}
      <div style={{ marginTop: 40 }}>
        <button
          onClick={() => {
            // 브라우저에서 직접 다운로드를 시작하도록 window.open 사용
            window.open(`https://lecture-sorter-backend.onrender.com/download/${uploadId}`, "_blank");
          }}
          style={{
            padding: "10px 20px",
            backgroundColor: "#4a90e2",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer"
          }}
        >
          📦 ZIP 전체 다운로드
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------
// 2) 메인 업로드 · 과제 등록 페이지
// ---------------------------------------------
function MainApp() {
  const [uploadId, setUploadId] = useState("");
  const [subject, setSubject] = useState("");
  const [week, setWeek] = useState("");
  const [files, setFiles] = useState([]);
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [assignmentDeadline, setAssignmentDeadline] = useState("");

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
      await axios.post(
        "https://lecture-sorter-backend.onrender.com/upload",
        formData
      );
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

      <button onClick={handleUpload} style={{ marginBottom: 30 }}>
        📤 업로드
      </button>

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

      <button onClick={handleRegisterAssignment} style={{ marginBottom: 30 }}>
        ✅ 과제 등록
      </button>

      {uploadId && (
        <div style={{ marginTop: "40px", borderTop: "1px solid #ccc", paddingTop: "30px" }}>
          <h3>📦 업로드 완료!</h3>
          <p>아래 링크로 언제든지 접속하여 확인할 수 있어요:</p>
          {/* 이제 HashRouter를 쓰므로 #/uploads/{uploadId} 경로를 앞에 붙여 줍니다 */}
          <a
            href={`https://lecture-sorter-frontend.onrender.com/#/uploads/${uploadId}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ wordBreak: "break-all", color: "blue" }}
          >
            https://lecture-sorter-frontend.onrender.com/#/uploads/{uploadId}
          </a>

          <h4 style={{ marginTop: "20px" }}>📱 QR코드로 공유</h4>
          <QRCodeCanvas
            value={`https://lecture-sorter-frontend.onrender.com/#/uploads/${uploadId}`}
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

// ---------------------------------------------
// 3) 전체 라우터 설정 (HashRouter)
// ---------------------------------------------
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/uploads/:uploadId" element={<UploadViewer />} />
      </Routes>
    </Router>
  );
}

export default App;