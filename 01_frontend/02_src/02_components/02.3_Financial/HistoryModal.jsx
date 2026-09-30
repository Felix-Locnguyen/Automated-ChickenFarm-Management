export default function HistoryModal({ records, onClose, onViewDetail }) {
  const sorted = [...records].sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div className="modal-overlay active" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">📋 Lịch sử giao dịch</h3>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="alerts-container" style={{ maxHeight: '400px' }}>
          {sorted.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#a0826d', padding: '24px 0' }}>Chưa có dữ liệu</p>
          ) : (
            sorted.map(rec => (
              <div key={rec.id} className="fin-record-card" onClick={() => onViewDetail(rec)}>
                <div className="fin-card-header">
                  <div className="fin-card-info">
                    <span className={`fin-card-type ${rec.type === 'income' ? 'type-income' : 'type-expense'}`}>
                      {rec.type === 'income' ? '💵 Thu' : '💸 Chi'}
                    </span>
                    <span style={{ fontSize: '13px', color: '#654321', fontWeight: 600 }}>
                      {rec.source || rec.expenseType}
                    </span>
                  </div>
                  <span className="fin-card-total">{rec.total?.toLocaleString('vi-VN')} ₫</span>
                </div>
                <div className="fin-card-details">
                  <span>📅 <b>{rec.date}</b></span>
                  {rec.coopName && <span>🏠 <b>{rec.coopName}</b></span>}
                </div>
              </div>
            ))
          )}
        </div>
        <button className="btn-primary" onClick={onClose}>Đóng</button>
      </div>
    </div>
  );
}
