export default function EnvironmentMonitor({ avgTemperature, avgHumidity, coops, activeAlertsCount }) {
  return (
    <div className="card-grid">
      <div className="card card-success">
        <div className="card-header">
          <span style={{ fontSize: '24px' }}>🐔</span>
          <span className="card-badge">Tổng đàn</span>
        </div>
        <h2 className="card-value">{coops.reduce((sum, c) => sum + c.chickens, 0).toLocaleString()}</h2>
        <p className="card-label">Con khỏe mạnh</p>
      </div>

      <div className={`card ${activeAlertsCount > 0 ? 'card-warning' : 'card-info'}`}>
        <div className="card-header">
          <span style={{ fontSize: '24px' }}>⚠️</span>
          <span className="card-badge">Cảnh báo</span>
        </div>
        <h2 className="card-value">{activeAlertsCount}</h2>
        <p className="card-label">{activeAlertsCount > 0 ? 'Cần chú ý' : 'Ổn định'}</p>
      </div>

      <div className="card card-default">
        <div className="card-header">
          <span style={{ fontSize: '24px' }}>🌡️</span>
          <span style={{ fontSize: '10px', backgroundColor: '#fef3c7', color: '#b45309', padding: '4px 8px', borderRadius: '8px', fontWeight: '600' }}>Trung bình</span>
        </div>
        <h2 className="card-value" style={{ color: '#654321' }}>{avgTemperature}</h2>
        <p className="card-label" style={{ color: '#a0826d' }}>Nhiệt độ trại</p>
      </div>

      <div className="card card-default">
        <div className="card-header">
          <span style={{ fontSize: '24px' }}>💧</span>
          <span style={{ fontSize: '10px', backgroundColor: '#e0f2fe', color: '#0369a1', padding: '4px 8px', borderRadius: '8px', fontWeight: '600' }}>Trung bình</span>
        </div>
        <h2 className="card-value" style={{ color: '#654321' }}>{avgHumidity}</h2>
        <p className="card-label" style={{ color: '#a0826d' }}>Độ ẩm không khí</p>
      </div>
    </div>
  );
}
