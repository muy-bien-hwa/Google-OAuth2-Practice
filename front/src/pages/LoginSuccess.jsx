import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import "../styles/LoginSuccess.css";

const LoginSuccess = () => {
    const navigate = useNavigate();

    useEffect(() => {
        console.log('✅ 로그인 성공! Dashboard로 이동합니다...');

        const timer = setTimeout(() => {
            navigate('/dashboard');
        }, 1000);

        return () => clearTimeout(timer);
    }, [navigate]);

    return (
        <div className="success-container">
            <div className="success-card">
                <div className="success-icon">✅</div>

                <h1 className="success-title">로그인 성공!</h1>

                <p className="success-desc">
                    잠시만 기다려주세요...
                </p>

                <div className="loading-spinner" />
            </div>
        </div>
    );
};

export default LoginSuccess;
