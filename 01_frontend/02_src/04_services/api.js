/**
 * Gọi API backend — mỗi hàm ứng với 1 endpoint.
 * Quy ước chung: hàm nào cần đăng nhập thì tự gắn JWT vào header.
 */
import { getToken, logout } from './auth';

const API_BASE = '/api'
/**
  - hàm bọc chung cho mọi request - tránh lặp code
  - Tự gắn header Content-Type + Authorization
  - Tự xử lý 401 (token hết hạn → đăng xuất luôn)
  - Tự parse JSON
 */

// Khai báo hàm và lấy Token
async function request(path, options = {}) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,   // spread: giữ nguyên method/body của từng hàm gọi
    headers: {
      'Content-Type': 'application/json',
      // Nếu có token thì gắn, không thì bỏ qua (route public như /sensor GET)
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  });

  // Token hết hạn / sai → backend trả 401 → đá về trang đăng nhập
  if (res.status === 401) {
    logout();
    window.location.reload();  // reload để App.jsx thấy isLoggedIn()=false → hiện LoginPage
    throw new Error('Phiên đăng nhập hết hạn');
  }

  if (!res.ok) {
    // Backend trả { detail: "..." } khi lỗi → ném ra để component hiển thị
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Lỗi ${res.status}`);
  }
  return res.json();
}


//                              Auth
// (đã có trong auth.js — không viết lại)





//                              Flock
export function fetchFlocks() {
  return request('/flocks');                        // GET /api/flocks — danh sách chuồng
}
export function createFlock(flock) {
  return request('/flocks', {
    method: 'POST',
    body: JSON.stringify(flock),                   // { name, chicken_count, breed... }
  });
}
export function updateFlock(id, flock) {
  return request(`/flocks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(flock),
  });
}
export function deleteFlock(id) {
  return request(`/flocks/${id}`, { method: 'DELETE' });
}


//                          Sensor
export function fetchReadings(limit = 100) {
  return request(`/sensor?limit=${limit}`);
}
export function createReading(reading) {
  return request('/sensor', {
    method: 'POST',
    body: JSON.stringify(reading),                 // { temperature, humidity, food_level, water_level, device_id }
  });
}
export function fetchLatestReading() {
  return request('/sensors/latest');
}


//                         Feeding
export function fetchFeedingLogs(flockId) {
  return request(`/feeding${flockId ? `?flock_id=${flockId}` : ''}`);
}
export function createFeedingLog(log) {
  return request('/feeding', {
    method: 'POST',
    body: JSON.stringify(log),                     // { feed_type, amount_kg, scheduled_time, flock_id }
  });
}
export function completeFeedingLog(id) {
  return request(`/feeding/${id}/complete`, { method: 'PUT' });
}
export function deleteFeedingLog(id) {
  return request(`/feeding/${id}`, { method: 'DELETE' });  // xóa lịch cho ăn
}




//                         HEALTH
export function fetchHealthRecords(flockId) {
  return request(`/health${flockId ? `?flock_id=${flockId}` : ''}`);
}
export function createHealthRecord(record) {
  return request('/health', {
    method: 'POST',
    body: JSON.stringify(record),
  });
}



//                         FINANCIAL
export function fetchFinancialRecords(flockId) {
  return request(`/financial${flockId ? `?flock_id=${flockId}` : ''}`);
}
export function createFinancialRecord(record) {
  return request('/financial', {
    method: 'POST',
    body: JSON.stringify(record),
    // Backend tự tính revenue/profit — mình chỉ gửi input
  });
}
export function fetchFinancialSummary(flockId) {
  return request(`/financial/summary${flockId ? `?flock_id=${flockId}` : ''}`);
}
export function updateFinancialRecord(id, record) {
  return request(`/financial/${id}`, {
    method: 'PUT',
    body: JSON.stringify(record),
  });
}
export function deleteFinancialRecord(id) {
  return request(`/financial/${id}`, { method: 'DELETE' });
}


//                         DEVICES
export function fetchDevices(flockId) {
  return request(`/devices${flockId ? `?flock_id=${flockId}` : ''}`);
}
export function createDevice(device) {
  return request('/devices', {
    method: 'POST',
    body: JSON.stringify(device),                  // { name, type, flock_id }
  });
}
export function toggleDevice(deviceId) {
  return request(`/devices/${deviceId}/toggle`, { method: 'PUT' });
}


//                          ALERTS
export function fetchAlerts(resolved = false) {
  return request(`/alerts?resolved=${resolved}`);  // { coop_name, message, created_at... }
}
export function resolveAlert(id) {
  return request(`/alerts/${id}/resolve`, { method: 'PUT' });
}


//                          CAMERA
export function fetchLatestDetection() {
  return request('/camera/latest');        // { detection: {...} | null }
}


//                          ANALYTICS
export function fetchDashboard() {
  return request('/analytics/dashboard');           // { summary, recent_alerts }
}
export function fetchSensorHistory(deviceId, hours = 24) {
  const q = new URLSearchParams({ hours });
  if (deviceId) q.set('device_id', deviceId);
  return request(`/analytics/sensor-history?${q}`);
}