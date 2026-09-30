export default function AlertPanel({ alerts, activeAlertsCount, show, onClose }) {
  return (
    <div className="modal-overlay active">
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">
            <span>⚠️</span>
            Cảnh báo hệ thống
          </h3>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="alerts-container">
          {alerts.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '14px', padding: '24px 0' }}>Tuyệt vời! Hệ thống ổn định.</p>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} className="alert-item">
                <div className="alert-header">
                  <span className="alert-coop">{alert.coopName}</span>
                  <span className="alert-time">{alert.time}</span>
                </div>
                <p className="alert-message">{alert.message}</p>
              </div>
            ))
          )}
        </div>
        <button className="btn-primary" onClick={onClose}>Đã hiểu</button>
      </div>
    </div>
  );
}
