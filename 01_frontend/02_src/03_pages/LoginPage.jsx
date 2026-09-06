import { useState } from 'react';
import { findUserByEmail } from '../04_services/users.js';
import { verifyPassword } from '../04_services/auth.js';

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (!email || !password) {
      setError('Vui lòng nhập đầy đủ thông tin');
      setLoading(false);
      return;
    }

    const user = findUserByEmail(email);
    if (!user) {
      setError('Sai tên tài khoản hoặc mật khẩu');
      setLoading(false);
      return;
    }

    const valid = await verifyPassword(password, user.passwordHash);
    if (!valid) {
      setError('Sai tên tài khoản hoặc mật khẩu');
      setLoading(false);
      return;
    }

    onLogin(user);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">🐔</div>
        <h1 className="login-title">Quản Lý Trang Trại Gà</h1>
        <p className="login-subtitle">Đăng nhập để quản lý trang trại</p>

        <form onSubmit={handleSubmit}>
          {error && <div className="login-error">{error}</div>}

          <div className="login-field">
            <label>Email</label>
            <input
              type="email"
              placeholder="admin55@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <label>Mật khẩu</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="login-btn"
            disabled={loading}
          >
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>
      </div>
    </div>
  );
}
