/**
 * Xác thực: gọi API backend, lưu JWT vào localStorage.
 *
 * localStorage: "kho" lưu dữ liệu của trình duyệt —
 * lưu ở đây thì F5 (reload trang) mất đăng nhập.
 * (Đây chính là lý do người dùng quen gọi nó là "giữ đăng nhập")
 */

const API_BASE = "/api" //  không cần viết http://localhost8000 nhờ proxy 



/** Đăng ký. Trả về { ok, message } để LoginPage hiển thị. */
export async function register(email, password, fullName)
/**
 * Quy trình đăng ký tài khoản:
 * 1. Nhận thông tin từ người dùng (email, password, fullName).
 * 2. Gửi request dạng POST lên Backend để server đối chiếu và lưu vào Database.
 * 3. Chờ server phản hồi kết quả (dùng 'await').
 * 4. Trả về đối tượng gồm trạng thái (ok) và thông báo (message) để LoginPage hiển thị.
 */
{
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // JSON.stringify: object → chuỗi JSON (vì fetch chỉ gửi chuỗi/text)
    body: JSON.stringify({ email, password, full_name: fullName }),
  });

  const data = await res.json();
  // res.ok = true nếu status 200-299; 400 (email trùng) → ok=false
  return { ok: res.ok, message: data.detail || 'Đăng ký thành công' };
}



/** Đăng nhập. Thành công → lưu token + trả về user info cho App.jsx. */
export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();

  if (!res.ok) {
    return { ok: false, message: data.detail || 'Đăng nhập thất bại' };
  };

  // Lưu token vào localStorage — key tùy mình đặt
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('userEmail', email);
  return { ok: true, message: 'Đăng nhập thành công' };
}

/** Lấy token đã lưu (null nếu chưa đăng nhập). */
export function getToken() {
  return localStorage.getItem('token');
}

/** Đăng xuất: xóa sạch thông tin đã lưu. */
export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('userEmail');
}


/** Kiểm tra "đã đăng nhập chưa" — App.jsx dùng để quyết định hiện LoginPage. */
export function isLoggedIn() {
  return !!getToken();  // !! chuyển string → boolean (null → false, "abc" → true)
}