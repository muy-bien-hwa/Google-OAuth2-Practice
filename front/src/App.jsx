/**
 * React 메인 App 컴포넌트
 * 라우팅 설정
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import LoginSuccess from './pages/LoginSuccess';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Routes>
      {/* 기본 경로 - 로그인 페이지로 리다이렉트 */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* 로그인 페이지 */}
      <Route path="/login" element={<Login />} />

      {/* 로그인 성공 페이지 (백엔드에서 리다이렉트) */}
      <Route path="/login/success" element={<LoginSuccess />} />

      {/* Dashboard */}
      <Route path="/dashboard" element={<Dashboard />} />

      {/* 404 페이지 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}


/**
 * 404 Not Found 페이지
 */
const NotFound = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      <h1 style={{ fontSize: '72px', margin: '0' }}>404</h1>
      <p style={{ fontSize: '24px', color: '#666' }}>페이지를 찾을 수 없습니다</p>
      <a
        href="/"
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          backgroundColor: '#4285f4',
          color: 'white',
          textDecoration: 'none',
          borderRadius: '4px'
        }}
      >
        홈으로 가기
      </a>
    </div>
  );
};


export default App;


// ========================================
// 💡 라우팅 구조
// ========================================
//
// /                  → /login으로 리다이렉트
// /login             → 로그인 페이지 (구글 로그인 버튼)
// /login/success     → 로그인 성공 페이지 (백엔드에서 리다이렉트)
// /dashboard         → 사용자 정보 표시
//
// 흐름:
// 1. 사용자가 /login 접속
// 2. "구글 로그인" 버튼 클릭
// 3. 백엔드 /auth/google/login으로 이동 (페이지 전환)
// 4. 구글 로그인 페이지로 리다이렉트
// 5. 로그인 완료 후 백엔드 /auth/google/callback으로 리다이렉트
// 6. 백엔드가 /login/success로 리다이렉트 (쿠키 설정)
// 7. /login/success에서 /dashboard로 이동
// 8. Dashboard에서 사용자 정보 표시