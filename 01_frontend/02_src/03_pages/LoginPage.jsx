import { useState } from 'react';
import { login, register } from '../04_services/auth';

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');     // cho chế độ đăng ký
  const [mode, setMode] = useState('login');        // 'login' | 'register'
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault(); // chặn form reload trang mặc định
    setError('');

     // Validate đơn giản phía client (backend cũng sẽ validate lần nữa)
    if (!email || !password) {
      setError('Vui lòng nhập đầy đủ thông tin');
      setLoading(false);
      return;
    }

    setLoading(true); // hiện trạng thái đang xử lý
    try {
        const result = mode === 'login'
          ? await login(email, password)
          : await register(email, password, fullName);

        if (!result.ok) {
          setError(result.message);  // ví dụ: "Email đã tồn tại", "Sai email hoặc mật khẩu"
          return;
        }
        if (mode === 'register') {
          // Đăng ký xong → tự chuyển sang màn đăng nhập
          setMode('login');
          setError('');
          alert('Đăng ký thành công! Vui lòng đăng nhập.');
          return;
        }
        // Đăng nhập thành công → báo cho App.jsx (kèm tên để hiện ở header)
        onLogin({ email, fullName: localStorage.getItem('userFullName') || '' });
      } catch (err) {
        // fetch ném lỗi khi MẤT MẠNG hoặc backend sập
        setError('Không kết nối được máy chủ. Hãy kiểm tra backend đã chạy chưa?');
      } finally {
        setLoading(false);          // luôn chạy, dù thành công hay lỗi
      }
  };
  return (
    <div className="login-page">
      {/* flex-col: các phần xếp DỌC, căn giữa — style ở App.css (.login-card...) */}
      <form onSubmit={handleSubmit} className="login-card">
        <div className="login-logo">🐔</div>
        <h1 className="login-title">Trang Trại Gà Thông Minh</h1>
        <p className="login-subtitle">
          {mode === 'login' ? 'Đăng nhập để quản lý trang trại' : 'Tạo tài khoản mới'}
        </p>

        {mode === 'register' && (
          <div className="login-field">
            <label>Họ và tên</label>
            <input
              type="text"
              placeholder="Họ và tên (VD: Nguyễn Văn A)"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
        )}
        <div className="login-field">
          <label>Email</label>
          <input
            type="email"
            placeholder="vidu@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="login-field">
          <label>Mật khẩu</label>
          <input
            type="password"
            placeholder="Nhập mật khẩu"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <p className="login-error">{error}</p>}

        <button type="submit" className="login-btn" disabled={loading}>
          {loading ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập' : 'Đăng ký'}
        </button>

        <p className="login-switch" onClick={() => {
          setMode(mode === 'login' ? 'register' : 'login');
          setError('');
        }}>
          {mode === 'login'
            ? 'Chưa có tài khoản? Đăng ký'
            : 'Đã có tài khoản? Đăng nhập'}
        </p>
      </form>
    </div>
  );
}

/* note
 e.preventDefault() — form HTML mặc định submit → reload trang → mất hết state React. Bắt buộc chặn trong SPA.
 2. loading state — tránh người dùng bấm nút 10 lần vì tưởng chưa nhận lệnh.
 3. finally — block chạy LUÔN LUÔN (kể cả khi có exception) → lý tưởng để tắt spinner.
*/
