import { useState } from 'react';

export default function DeleteCoopModal({ coopName, show, onClose, onDelete }) {
  const [code, setCode] = useState('');
  const [confirmCode] = useState(() => Math.floor(1000 + Math.random() * 9000));
  const [error, setError] = useState(false);

  if (!show) return null;

  const handleConfirm = () => {
    if (Number(code) === confirmCode) {
      onDelete();
      setCode('');
      setError(false);
    } else {
      setError(true);
    }
  };

  const handleClose = () => {
    setCode('');
    setError(false);
    onClose();
  };

  return (
    <div className="modal-overlay active" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">🗑️ Xóa dữ liệu chuồng</h3>
          <button className="close-btn" onClick={handleClose}>✕</button>
        </div>

        <p style={{ fontSize: '13px', color: '#654321', margin: '0 0 12px 0' }}>
          Nhập mã <b>{confirmCode}</b> để xác nhận xóa toàn bộ dữ liệu <b>{coopName}</b>
        </p>

        <div className="confirm-code">{confirmCode}</div>

        <input
          className="confirm-input"
          type="number"
          placeholder="Nhập mã xác nhận..."
          value={code}
          onChange={(e) => { setCode(e.target.value); setError(false); }}
        />

        {error && (
          <p style={{ color: '#dc2626', fontSize: '12px', textAlign: 'center', margin: '8px 0' }}>
            Sai mã xác nhận!
          </p>
        )}

        <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
          <button className="btn-confirm-delete" onClick={handleConfirm}>Xóa</button>
          <button className="btn-cancel-delete" onClick={handleClose}>Hủy</button>
        </div>
      </div>
    </div>
  );
}
