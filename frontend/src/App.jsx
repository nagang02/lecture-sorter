import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [uploadId, setUploadId] = useState('');
  const [subject, setSubject] = useState('');
  const [week, setWeek] = useState('');
  const [files, setFiles] = useState([]);
  const [assignTitle, setAssignTitle] = useState('');
  const [assignDeadline, setAssignDeadline] = useState('');
  const [uploadedData, setUploadedData] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [message, setMessage] = useState('');

  const backendURL = 'https://lecture-sorter-backend.onrender.com';

  const handleUpload = async () => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('upload_id', uploadId);
    formData.append('subject', subject);
    formData.append('week', week);

    try {
      const res = await axios.post(`${backendURL}/upload`, formData);
      setMessage('파일 업로드 성공');
      console.log(res.data);
    } catch (err) {
      console.error(err);
      setMessage('업로드 실패');
    }
  };

  const handleAssignment = async () => {
    const formData = new FormData();
    formData.append('upload_id', uploadId);
    formData.append('subject', subject);
    formData.append('title', assignTitle);
    formData.append('deadline', assignDeadline);

    try {
      await axios.post(`${backendURL}/assignments`, formData);
      setMessage('과제 등록 완료');
    } catch (err) {
      console.error(err);
      setMessage('과제 등록 실패');
    }
  };

  const fetchUploadedData = async () => {
    try {
      const res = await axios.get(`${backendURL}/uploads/${uploadId}`);
      setUploadedData(res.data);
      setMessage('');
    } catch (err) {
      console.error(err);
      setMessage('업로드된 자료 없음');
      setUploadedData(null);
    }
  };

  const fetchAssignments = async () => {
    try {
      const res = await axios.get(`${backendURL}/assignments/${uploadId}`);
      setAssignments(res.data);
      setMessage('');
    } catch (err) {
      console.error(err);
      setMessage('과제 정보 없음');
      setAssignments([]);
    }
  };

  const handleDownloadZip = async () => {
    try {
      const res = await axios.get(`${backendURL}/zip/${uploadId}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${uploadId}_자료.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      setMessage('ZIP 다운로드 실패');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>📚 Lecture Sorter</h1>

      <input
        placeholder="업로드 ID"
        value={uploadId}
        onChange={(e) => setUploadId(e.target.value)}
      />
      <input
        placeholder="과목명"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
      />
      <input
        placeholder="주차 (숫자만)"
        value={week}
        onChange={(e) => setWeek(e.target.value)}
      />
      <input
        type="file"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files))}
      />
      <button onClick={handleUpload}>📤 파일 업로드</button>

      <hr />

      <input
        placeholder="과제 제목"
        value={assignTitle}
        onChange={(e) => setAssignTitle(e.target.value)}
      />
      <input
        type="date"
        value={assignDeadline}
        onChange={(e) => setAssignDeadline(e.target.value)}
      />
      <button onClick={handleAssignment}>📝 과제 등록</button>

      <hr />

      <button onClick={fetchUploadedData}>📂 업로드 내용 보기</button>
      <button onClick={fetchAssignments}>📋 과제 목록 보기</button>
      <button onClick={handleDownloadZip}>⬇ ZIP 다운로드</button>

      <p style={{ color: 'green' }}>{message}</p>

      {uploadedData && (
        <div>
          <h2>업로드 파일 목록</h2>
          {Object.entries(uploadedData).map(([subj, weeks]) => (
            <div key={subj}>
              <strong>{subj}</strong>
              <ul>
                {Object.entries(weeks).map(([week, files]) => (
                  <li key={week}>
                    {week}: {files.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {assignments.length > 0 && (
        <div>
          <h2>과제 목록</h2>
          <ul>
            {assignments.map((a, idx) => (
              <li key={idx}>
                [{a.subject}] {a.title} - 마감일: {a.deadline}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
