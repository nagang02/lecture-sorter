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
// 1) 업로드 결과 보기 컴포넌트
// ---------------------------------------------
function UploadViewer() {
  const { uploadId } = useParams();
  const [uploadedData, setUploadedData] = useState(null);

  // 백엔드에서 파일 목록을 가져오는 함수
  const fetchData = () => {
    axios
      .get(`https://lecture-sorter-backend.onrender.com/uploads/${uploadId}`)
      .then((res) => setUploadedData(res.data))
      .catch((err) => {
        console.error("데이터 로딩 에러:", err);
        setUploadedData({ error: true });
      });
  };

  // 페이지가 처음 열릴 때 데이터를 가져옵니다.
  useEffect(() => {
    fetchData();
  }, [uploadId]);

  // 삭제 버튼을 눌렀을 때 실행될 함수
  const handleDelete = (subject, week, fileName) => {
    if (!window.confirm(`'${fileName}' 파일을 정말 삭제하시겠습니까?`)) {
      return;
    }

    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("week", week);
    formData.append("file_name", fileName);

    axios.post("https://lecture-sorter-backend.onrender.com/delete-file", formData)
      .then(response => {
        alert(response.data.message);
        fetchData(); // 목록을 다시 불러와 화면을 업데이트
      })
      .catch(error => {
        console.error("삭제 중 에러 발생:", error);
        alert("파일 삭제에 실패했습니다: " + (error.response?.data?.detail || "서버 에러"));
      });
  };

  if (!uploadedData) return <p>불러오는 중...</p>;
  if (uploadedData.error) return <p>업로드 정보를 불러오지 못했습니다. 올바른 ID인지 확인해주세요.</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20, fontFamily: "sans-serif", border: '1px solid #eee', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <h2>📂 업로드 ID: {uploadId}</h2>

      {Object.keys(uploadedData).length === 0 || (Object.keys(uploadedData).length === 1 && uploadedData.assignments) ? (
        <p>업로드된 파일이 없습니다.</p>
      ) : (
        Object.entries(uploadedData).map(([subject, weeks]) => {
          if (subject === "assignments") return null;
          return (
            <div key={subject} style={{ marginBottom: '20px' }}>
              <h3>과목: {subject}</h3>
              {Object.entries(weeks).map(([week, files]) => (
                <div key={week} style={{ marginLeft: 20, marginTop: '10px' }}>
                  <h4>{week}주차</h4>
                  <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
                    {files.map((fileName, idx) => (
                      <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', padding: '8px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                        <a
                          href={`https://lecture-sorter-backend.onrender.com/files/${uploadId}/${subject}/week_${week}/${fileName}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ textDecoration: 'none', color: '#007bff' }}
                        >
                          {fileName}
                        </a>
                        <button
                          onClick={() => handleDelete(subject, week, fileName)}
                          style={{ marginLeft: '10px', padding: '2px 8px', backgroundColor: '#ff4d4d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                        >
                          삭제
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          );
        })
      )}

      {uploadedData.assignments && uploadedData.assignments.length > 0 && (
        <div style={{ marginTop: 30, borderTop: "1px solid #ddd", paddingTop: 20 }}>
          <h3>📝 등록된 과제 목록</h3>
          <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
            {uploadedData.assignments.map((asgmt, idx) => (
              <li key={idx} style={{ marginBottom: '8px', padding: '8px', backgroundColor: '#f0f8ff', borderRadius: '4px' }}>
                <strong>[{asgmt.subject}]</strong> {asgmt.title} – <strong>기한:</strong> {asgmt.deadline}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 40 }}>
        <button
          onClick={() => {
            window.open(`https://lecture-sorter-backend.onrender.com/download/${uploadId}`, "_blank");
          }}
          style={{ padding: "10px 20px", backgroundColor: "#4a90e2", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: '16px' }}
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
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async () => {
    if (!uploadId || !subject || !week || files.length === 0) {
      alert("모든 항목을 입력하고 파일을 선택해주세요.");
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("week", week);
    for (const file of files) {
      formData.append("files", file);
    }

    try {
      await axios.post("https://lecture-sorter-backend.onrender.com/upload", formData);
      alert("업로드 성공!");
    } catch (error) {
      console.error("업로드 실패:", error);
      alert("업로드 실패");
    } finally {
      setIsUploading(false);
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
      await axios.post("https://lecture-sorter-backend.onrender.com/assignments", formData);
      alert("과제 등록 성공!");
      setAssignmentTitle("");
      setAssignmentDeadline("");
    } catch (error) {
      console.error("과제 등록 실패:", error);
      alert("과제 등록 실패");
    }
  };

  const commonInputStyle = { width: '100%', padding: '8px', marginBottom: '10px', border: '1px solid #ccc', borderRadius: '4px' };
  const commonButtonStyle = { width: '100%', padding: '10px', border: 'none', borderRadius: '4px', color: 'white', backgroundColor: '#007bff', cursor: 'pointer', fontSize: '16px' };

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20, fontFamily: "sans-serif" }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <h1>📚 Lecture Sorter</h1>
        <p>강의 자료를 손쉽게 정리하고 공유하세요.</p>
      </div>

      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #eee', borderRadius: '8px' }}>
        <h2>📤 파일 업로드</h2>
        <label>Upload ID:</label>
        <input type="text" value={uploadId} onChange={(e) => setUploadId(e.target.value.trim())} placeholder="예: my-cs-lectures (영어,숫자,-만 사용)" style={commonInputStyle} />
        <label>과목명:</label>
        <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="예: 디지털공학" style={commonInputStyle} />
        <label>주차:</label>
        <input type="text" value={week} onChange={(e) => setWeek(e.target.value)} placeholder="예: 10" style={commonInputStyle} />
        <label>강의 파일:</label>
        <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files))} style={{ width: "100%", marginBottom: 20, display: 'block' }} />
        <button onClick={handleUpload} style={commonButtonStyle} disabled={isUploading}>
          {isUploading ? "업로드 중..." : "업로드"}
        </button>
      </div>

      <div style={{ padding: '20px', border: '1px solid #eee', borderRadius: '8px' }}>
        <h2>📝 과제 등록</h2>
        <p style={{fontSize: '14px', color: '#666'}}>과제를 등록하려면 위 'Upload ID'와 '과목명'이 필요합니다.</p>
        <label>과제 제목:</label>
        <input type="text" value={assignmentTitle} onChange={(e) => setAssignmentTitle(e.target.value)} placeholder="예: 기말 프로젝트 제안서" style={commonInputStyle} />
        <label>제출 기한:</label>
        <input type="date" value={assignmentDeadline} onChange={(e) => setAssignmentDeadline(e.target.value)} style={commonInputStyle} />
        <button onClick={handleRegisterAssignment} style={{...commonButtonStyle, backgroundColor: '#28a745'}}>
          과제 등록
        </button>
      </div>

      {uploadId && (
        <div style={{ marginTop: "40px", borderTop: "1px solid #ccc", paddingTop: "30px", textAlign: 'center' }}>
          <h3>📦 업로드 완료 및 결과 확인</h3>
          <p>아래 링크나 QR코드로 언제든지 접속하여 확인할 수 있어요:</p>
          <a
            href={`#_blank`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ wordBreak: "break-all", color: "blue", display: 'block', margin: '10px 0' }}
          >
            {`https://lecture-sorter-frontend.onrender.com/#/uploads/${uploadId}`}
          </a>
          <div style={{ marginTop: '20px', display: 'inline-block' }}>
            <QRCodeCanvas
              value={`https://lecture-sorter-frontend.onrender.com/#/uploads/${uploadId}`}
              size={160}
              includeMargin={true}
            />
          </div>
          <p style={{ marginTop: "10px", color: "#888" }}>
            이 QR을 스캔하거나 링크를 즐겨찾기 해두면 편리해요!
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------
// 3) 전체 라우터 설정
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