import "../styles/Login.css";

const Login = () => {
    const handleGoogleLogin = () => {
        window.location.href = `${import.meta.env.VITE_BACKEND_URL}/auth/google/login`;
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h1 className="login-title">환영합니다! 👋</h1>

                <button
                    className="google-login-btn"
                    onClick={handleGoogleLogin}
                >
                    <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
                        <g fill="none" fillRule="evenodd">
                            <path d="M17.6 9.2l-.1-1.8H9v3.4h4.8C13.6 12 13 13 12 13.6v2.2h3a8.8 8.8 0 0 0 2.6-6.6z" fill="#FFF" />
                            <path d="M9 18c2.4 0 4.5-.8 6-2.2l-3-2.2a5.4 5.4 0 0 1-8-2.9H1V13a9 9 0 0 0 8 5z" fill="#FFF" />
                            <path d="M4 10.7a5.4 5.4 0 0 1 0-3.4V5H1a9 9 0 0 0 0 8l3-2.3z" fill="#FFF" />
                            <path d="M9 3.6c1.3 0 2.5.4 3.4 1.3L15 2.3A9 9 0 0 0 1 5l3 2.4a5.4 5.4 0 0 1 5-3.7z" fill="#FFF" />
                        </g>
                    </svg>
                    Google로 로그인
                </button>

                <p className="login-desc">
                    구글 계정으로 간편하게 로그인하세요
                </p>
            </div>
        </div>
    );
};

export default Login;
