import { useState } from 'react';

export default function CoopDetailView({ coop, onBack, onToggleDevice, onAddFeedSchedule, onRemoveFeedSchedule, onUpdateThresholds }) {
  const [showAddFeed, setShowAddFeed] = useState(false);
  const [newFeed, setNewFeed] = useState({ time: '', amount: '', type: 'Sáng' });
  const [thresholds, setThresholds] = useState(coop.thresholds || { tempMin: 20, tempMax: 35, humMin: 40, humMax: 80 });

  const handleAddFeed = () => {
    if (newFeed.time && newFeed.amount) {
      onAddFeedSchedule(coop.id, newFeed);
      setNewFeed({ time: '', amount: '', type: 'Sáng' });
      setShowAddFeed(false);
    }
  };

  const handleSaveThresholds = () => {
    onUpdateThresholds(coop.id, thresholds);
  };

  return (
    <div>
      <button className="back-btn" onClick={onBack}>← Quay lại</button>

      <div className="camera-grid">
        <div className="camera-view">
          <div className="camera-status">
            <span className={`dot ${coop.devices?.camera ? 'online' : 'offline'}`}></span>
            <span>{coop.devices?.camera ? '🟢 Trực tiếp' : '⚫ Đã tắt'}</span>
          </div>
          <div className="camera-feed">
            {coop.devices?.camera ? '📹 Camera 1 hoạt động' : '📹 Camera 1 tắt'}
          </div>
        </div>
        <div className="camera-view">
          <div className="camera-status">
            <span className={`dot ${coop.devices?.camera ? 'online' : 'offline'}`}></span>
            <span>{coop.devices?.camera ? '🟢 Trực tiếp' : '⚫ Đã tắt'}</span>
          </div>
          <div className="camera-feed">
            {coop.devices?.camera ? '📹 Camera 2 hoạt động' : '📹 Camera 2 tắt'}
          </div>
        </div>
      </div>

      <div className="card-grid">
        <div className="card card-default">
          <span style={{ fontSize: '24px', marginBottom: '8px', display: 'block' }}>🌡️</span>
          <p style={{ fontSize: '11px', color: '#a0826d', margin: 0 }}>Nhiệt độ</p>
          <p style={{ fontSize: '18px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.temperature}°C</p>
        </div>
        <div className="card card-default">
          <span style={{ fontSize: '24px', marginBottom: '8px', display: 'block' }}>💧</span>
          <p style={{ fontSize: '11px', color: '#a0826d', margin: 0 }}>Độ ẩm</p>
          <p style={{ fontSize: '18px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.humidity}%</p>
        </div>
        <div className="card card-default">
          <span style={{ fontSize: '24px', marginBottom: '8px', display: 'block' }}>🌾</span>
          <p style={{ fontSize: '11px', color: '#a0826d', margin: 0 }}>Thức ăn</p>
          <p style={{ fontSize: '18px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.foodLevel}%</p>
        </div>
        <div className="card card-default">
          <span style={{ fontSize: '24px', marginBottom: '8px', display: 'block' }}>💧</span>
          <p style={{ fontSize: '11px', color: '#a0826d', margin: 0 }}>Nước uống</p>
          <p style={{ fontSize: '18px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.waterLevel}%</p>
        </div>
      </div>

      <h3 className="section-title">⚙️ Điều khiển Thiết bị</h3>
      <div className="device-grid">
        {[
          { key: 'fan', label: 'Quạt thông gió', icon: '💨' },
          { key: 'light', label: 'Đèn sưởi', icon: '💡' },
          { key: 'camera', label: 'Camera', icon: '📷' },
          { key: 'feeder', label: 'Máy cho ăn', icon: '🌾' }
        ].map(device => (
          <div key={device.key} className="device-toggle">
            <div className="device-label">
              <span style={{ fontSize: '18px' }}>{device.icon}</span>
              <div>
                <p className="device-name">{device.label}</p>
                <p className="device-status">{coop.devices?.[device.key] ? 'Bật' : 'Tắt'}</p>
              </div>
            </div>
            <button
              className={`toggle-switch ${coop.devices?.[device.key] ? 'active' : ''}`}
              onClick={() => onToggleDevice(coop.id, device.key)}
            >
              <div className="toggle-thumb"></div>
            </button>
          </div>
        ))}
      </div>

      {/* LỊCH CHO ĂN UỐNG */}
      <div className="feed-schedule">
        <div className="feed-schedule-header">
          <h3 className="section-title" style={{ margin: 0 }}>🍽️ Lịch cho ăn uống</h3>
          <button className="btn-add" onClick={() => setShowAddFeed(!showAddFeed)}>
            {showAddFeed ? '✕' : '+'}
          </button>
        </div>

        {showAddFeed && (
          <div className="feed-form">
            <div className="feed-form-row">
              <div className="feed-form-group">
                <label>Loại</label>
                <select
                  value={newFeed.type}
                  onChange={(e) => setNewFeed({ ...newFeed, type: e.target.value })}
                >
                  <option value="Sáng">Sáng</option>
                  <option value="Trưa">Trưa</option>
                  <option value="Chiều">Chiều</option>
                  <option value="Tối">Tối</option>
                </select>
              </div>
              <div className="feed-form-group">
                <label>Giờ</label>
                <input
                  type="time"
                  value={newFeed.time}
                  onChange={(e) => setNewFeed({ ...newFeed, time: e.target.value })}
                />
              </div>
              <div className="feed-form-group">
                <label>Lượng (kg)</label>
                <input
                  type="number"
                  placeholder="50"
                  value={newFeed.amount}
                  onChange={(e) => setNewFeed({ ...newFeed, amount: e.target.value })}
                />
              </div>
            </div>
          </div>
        )}

        <div className="feed-list">
          {coop.feedingSchedule && coop.feedingSchedule.length > 0 ? (
            coop.feedingSchedule.map(schedule => (
              <div key={schedule.id} className="feed-item">
                <div className="feed-item-info">
                  <span className="feed-time">⏰ {schedule.time}</span>
                  <span className="feed-type">{schedule.type}</span>
                  <span className="feed-amount">{schedule.amount} kg</span>
                </div>
                <button className="btn-remove-feed" onClick={() => onRemoveFeedSchedule(coop.id, schedule.id)}>✕</button>
              </div>
            ))
          ) : (
            <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '13px', padding: '12px 0' }}>Chưa có lịch cho ăn</p>
          )}
        </div>
      </div>

      {/* MỨC CẢNH BÁO */}
      <div className="threshold-settings">
        <h3 className="section-title">⚠️ Mức cảnh báo</h3>

        <div className="threshold-section">
          <p className="threshold-label">🌡️ Nhiệt độ (°C)</p>
          <div className="threshold-row">
            <div className="threshold-input">
              <label>Min</label>
              <input
                type="number"
                value={thresholds.tempMin}
                onChange={(e) => setThresholds({ ...thresholds, tempMin: Number(e.target.value) })}
              />
            </div>
            <div className="threshold-input">
              <label>Max</label>
              <input
                type="number"
                value={thresholds.tempMax}
                onChange={(e) => setThresholds({ ...thresholds, tempMax: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>

        <div className="threshold-section">
          <p className="threshold-label">💧 Độ ẩm (%)</p>
          <div className="threshold-row">
            <div className="threshold-input">
              <label>Min</label>
              <input
                type="number"
                value={thresholds.humMin}
                onChange={(e) => setThresholds({ ...thresholds, humMin: Number(e.target.value) })}
              />
            </div>
            <div className="threshold-input">
              <label>Max</label>
              <input
                type="number"
                value={thresholds.humMax}
                onChange={(e) => setThresholds({ ...thresholds, humMax: Number(e.target.value) })}
              />
            </div>
          </div>
        </div>

        <button className="btn-save-threshold" onClick={handleSaveThresholds}>Lưu mức cảnh báo</button>
      </div>

      <div className="card card-default" style={{ padding: '16px' }}>
        <h3 className="section-title" style={{ marginBottom: '12px' }}>📊 Thống kê</h3>
        <div className="stats-grid">
          {Object.entries(coop.stats || {}).map(([key, val]) => (
            <div key={key} className="stats-item">
              <p style={{ fontSize: '10px', color: '#a0826d', margin: 0 }}>
                {key === 'dailyEggs' ? 'Trứng' : key === 'mortalityRate' ? 'Tỷ lệ chết' : 'Thức ăn'}
              </p>
              <p style={{ fontSize: '12px', fontWeight: '700', color: '#654321', margin: '4px 0 0 0' }}>{val || '0'}</p>
            </div>
          ))}
        </div>

        {coop.logs && coop.logs.length > 0 && (
          <>
            <p style={{ fontSize: '11px', fontWeight: '600', color: '#654321', margin: '12px 0 8px 0' }}>Nhật ký hôm nay:</p>
            {coop.logs.map((log, idx) => (
              <div key={idx} className="log-item">
                <span className="log-time">{log.time}</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
