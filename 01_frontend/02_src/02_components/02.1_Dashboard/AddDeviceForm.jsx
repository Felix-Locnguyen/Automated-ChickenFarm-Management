import { useState } from 'react';
import { createDevice } from '../../04_services/api';

/**
 * B10 — form thêm thiết bị (tab ⚙️ Thiết bị).
 * Trước đây web không có form này → phải chèn thiết bị qua curl/test mới thấy QR.
 * Tạo xong App hiện toast + tab tự mở modal QR → flow: thêm → QR → in/dán → ghép.
 */
export default function AddDeviceForm({ coops, onAdded, onError }) {
  const [name, setName] = useState('');
  const [type, setType] = useState('camera');
  const [flockId, setFlockId] = useState('');   // '' = chưa gán (vô chủ, ghép QR sau)
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    try {
      const device = await createDevice({
        name: name.trim(),
        type,
        flock_id: flockId ? Number(flockId) : null,   // B6: null = chưa thuộc ai → ghép QR
      });
      onAdded(device);
    } catch (err) {
      onError(err.message);   // vd 404 che giấu "Không tồn tại hoặc bạn không có quyền"
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="feed-form" style={{ marginBottom: 16 }}>
      <div className="feed-form-row">
        <div className="feed-form-group">
          <label>Tên thiết bị</label>
          <input
            type="text"
            placeholder="VD: Camera chuồng A"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="feed-form-group">
          <label>Loại</label>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="camera">📷 Camera</option>
            <option value="fan">💨 Quạt thông gió</option>
            <option value="light">💡 Đèn sưởi</option>
            <option value="feeder">🌾 Máy cho ăn</option>
            <option value="sensor">🌡️ Cảm biến</option>
          </select>
        </div>
        <div className="feed-form-group">
          <label>Chuồng</label>
          <select value={flockId} onChange={(e) => setFlockId(e.target.value)}>
            <option value="">Chưa gán — ghép QR sau</option>
            {coops.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="feed-form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button
            type="submit"
            className="login-btn"
            disabled={busy || !name.trim()}
            style={{ padding: '10px 20px' }}
          >
            {busy ? 'Đang thêm...' : '＋ Thêm'}
          </button>
        </div>
      </div>
    </form>
  );
}
