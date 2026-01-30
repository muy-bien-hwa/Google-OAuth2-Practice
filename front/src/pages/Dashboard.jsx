import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/Dashboard.css';

const Dashboard = () => {
    const navigate = useNavigate();

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const response = await axios.get(
                    'http://localhost:8000/auth/me',
                    { withCredentials: true }
                );
                setUser(response.data);
            } catch (err) {
                if (err.response?.status === 401) {
                    setError('로그인이 필요합니다.');
                    setTimeout(() => navigate('/login'), 2000);
                } else {
                    setError('사용자 정보를 가져오는데 실패했습니다.');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchUserInfo();
    }, [navigate]);

    const handleLogout = async () => {
        try {
            await axios.post(
                `${import.meta.env.VITE_BACKEND_URL}/auth/logout`,
                {},
                { withCredentials: true }
            );
        } finally {
            navigate('/login');
        }
    };

    if (loading) {
        return (
            <div className="center-screen">
                <div className="loading-box">
                    <div className="spinner" />
                    <p>사용자 정보를 불러오는 중...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="center-screen">
                <div className="error-box">
                    <p>❌ {error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            <div className="dashboard-card">

                <header className="dashboard-header">
                    <h1>Dashboard</h1>
                    <button className="logout-btn" onClick={handleLogout}>
                        로그아웃
                    </button>
                </header>

                {user && (
                    <div className="user-section">
                        <h2>환영합니다, {user.name}님! 👋</h2>

                        <div className="user-card">
                            <div className="field">
                                <strong>사용자 ID</strong>
                                <div className="value mono">{user.id}</div>
                            </div>

                            <div className="field">
                                <strong>이메일</strong>
                                <div className="value">{user.email}</div>
                            </div>

                            <div className="field">
                                <strong>이름</strong>
                                <div className="value">{user.name}</div>
                            </div>
                        </div>

                        <div className="info-box">
                            <strong>💡 정보</strong>
                            <p>
                                이 정보는 JWT 토큰에서 추출되었습니다.
                                토큰은 HttpOnly 쿠키에 저장되어
                                JavaScript로 직접 접근할 수 없습니다.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
