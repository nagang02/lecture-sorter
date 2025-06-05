// src/App.jsx
import React, { useState } from "react";
import axios from "axios";

const BACKEND_URL = "https://lecture-sorter-backend.onrender.com";

function App() {
  const [uploadId, setUploadId] = useState("");
  const [subject, setSubject] = useState("");
  const [week, setWeek] = useState("");
  const [files, setFiles] = useState([]);
  const [title, setTitle] = useState("");
  const [deadline, setDeadline] = useState("");
  const [result, setResult] = useState(null);
  const [summary, setSummary] = useState(null);

  const handleFileChange = (e) => setFiles(e.target.files);

  const handleUpload = async () => {
    if (!uploadId || !subject || !week || files.length === 0) {
      alert("모든 정보를 입력해주세요");
      return;
    }
    const formData = new FormData();
    for (let file of files) formData.append("files", file);
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("week", week);
    const res = await axios.post(`${BACKEND_URL}/upload`, formData);
    setResult(res.data);
    alert("업로드 완료!");
  };

  const handleAssignment = async () => {
    if (!uploadId || !subject || !title || !deadline) {
      alert("모든 정보를 입력해주세요");
      return;
    }
    const formData = new FormData();
    formData.append("upload_id", uploadId);
    formData.append("subject", subject);
    formData.append("title", title);
    formData.append("deadline", deadline);
    const res = await axios.post(`${BACKEND_URL}/assignments`, formData);
    alert(res.data.message);
  };

  const handleView = async () => {
    const res = await axios.get(`${BACKEND_URL}/upload_summary/${uploadId}`);
    setSummary(res.data);
  };

  const handleDownload = () => {
    window.open(`${BACKEND_URL}/download_zip/${uploadId}`, "_blank");
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Lecture Sorter</h1>

      <input
        type="text"
        placeholder="고유 ID (예: my2025)"
        value={uploadId}
        onChange={(e) => setUploadId(e.target.value)}
        className="border p-2 mr-2"
      />
      <input
        type="text"
        placeholder="과목명"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        className="border p-2 mr-2"
      />
      <input
        type="text"
        placeholder="주차"
        value={week}
        onChange={(e) => setWeek(e.target.value)}
        className="border p-2 mr-2"
      />
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        className="my-2"
      />
      <button onClick={handleUpload} className="bg-blue-500 text-white p-2 rounded">
        파일 업로드
      </button>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">과제 등록</h2>
        <input
          type="text"
          placeholder="과제 제목"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="border p-2 mr-2"
        />
        <input
          type="text"
          placeholder="제출기한 (예: 2025-06-10)"
          value={deadline}
          onChange={(e) => setDeadline(e.target.value)}
          className="border p-2 mr-2"
        />
        <button onClick={handleAssignment} className="bg-green-500 text-white p-2 rounded">
          과제 등록
        </button>
      </div>

      <div className="mt-6">
        <button onClick={handleView} className="bg-gray-700 text-white p-2 rounded mr-2">
          업로드 내용 보기
        </button>
        <button onClick={handleDownload} className="bg-purple-600 text-white p-2 rounded">
          Zip 다운로드
        </button>
      </div>

      {summary && (
        <div className="mt-4">
          <h3 className="text-lg font-bold">📄 파일 요약</h3>
          <ul className="list-disc pl-5">
            {summary.files.map((f, idx) => (
              <li key={idx}>
                <strong>{f.filename}</strong>: {f.summary.slice(0, 100)}
              </li>
            ))}
          </ul>
          <h3 className="text-lg font-bold mt-4">📝 과제 목록</h3>
          <ul className="list-disc pl-5">
            {summary.assignments.map((a, idx) => (
              <li key={idx}>
                {a.subject} - {a.title} (기한: {a.deadline})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
