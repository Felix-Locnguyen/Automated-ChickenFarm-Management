export default function CoopsList({ coops, onSelectCoop }) {
  return (
    <div>
      {coops.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '14px', padding: '20px' }}>Chưa có dữ liệu chuồng</p>
      ) : (
        coops.map(coop => {
          const isWarning = coop.status === 'warning';
          return (
            <div
              key={coop.id}
              className="coop-card"
              onClick={() => onSelectCoop(coop)}
            >
              <div className="coop-header">
                <div className="coop-name">
                  <span className={`status-dot ${isWarning ? 'warning' : ''}`}></span>
                  <h4>{coop.name}</h4>
                </div>
                <span style={{ fontSize: '12px', fontWeight: '600', color: isWarning ? '#c2410c' : '#16a34a' }}>
                  {isWarning ? 'Cảnh báo' : 'Bình thường'}
                </span>
              </div>
              <div className="coop-stats">
                <div>
                  <p className="stat-item">Gà</p>
                  <p className="stat-value">{coop.chickens > 0 ? coop.chickens.toLocaleString('vi-VN') : '0'}</p>
                </div>
                <div>
                  <p className="stat-item">Nhiệt độ</p>
                  <p className="stat-value">{coop.temperature}°C</p>
                </div>
                <div>
                  <p className="stat-item">Độ ẩm</p>
                  <p className="stat-value">{coop.humidity}%</p>
                </div>
                <div>
                  <p className="stat-item">Thức ăn</p>
                  <p className="stat-value">{coop.foodLevel}%</p>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#a0826d', marginBottom: '4px' }}>
                <span>🌾 Thức ăn: {coop.foodLevel}%</span>
                <span>💧 Nước: {coop.waterLevel}%</span>
              </div>
              <div className="progress-bar">
                <div
                  className={`progress-fill ${coop.foodLevel < 30 ? 'warning' : ''}`}
                  style={{ width: `${coop.foodLevel}%` }}
                ></div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
