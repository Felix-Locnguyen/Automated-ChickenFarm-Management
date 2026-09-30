import { useState } from 'react';
import FeedingControl from '../02.1_Dashboard/FeedingControl.jsx';

export default function CageViewer({ coop, onBack, onToggleDevice, onAddFeedSchedule, onRemoveFeedSchedule, onUpdateThresholds, onUpdateCoop }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(coop.name);
  const [editChickens, setEditChickens] = useState(coop.chickens);

  const handleSave = () => {
    if (editName.trim()) {
      onUpdateCoop(coop.id, editName.trim(), editChickens);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditName(coop.name);
    setEditChickens(coop.chickens);
    setIsEditing(false);
  };

  return (
    <div>
      <button className="back-btn" onClick={onBack}>← Quay lại</button>

      <div className="coop-edit-header">
        {isEditing ? (
          <div className="coop-edit-form">
            <input
              type="text"
              className="coop-edit-name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="Tên chuồng"
            />
            <input
              type="number"
              className="coop-edit-chickens"
              value={editChickens}
              onChange={(e) => setEditChickens(e.target.value)}
              placeholder="Số lượng gà"
            />
            <div className="coop-edit-actions">
              <button className="coop-edit-save" onClick={handleSave}>💾 Lưu</button>
              <button className="coop-edit-cancel" onClick={handleCancel}>✕ Hủy</button>
            </div>
          </div>
        ) : (
          <div className="coop-edit-display">
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.name}</h2>
              <p style={{ fontSize: '12px', color: '#a0826d', margin: '4px 0 0 0' }}>🐔 {coop.chickens?.toLocaleString('vi-VN')} con</p>
            </div>
            <button className="coop-edit-btn" onClick={() => setIsEditing(true)}>✏️</button>
          </div>
        )}
      </div>

      <div className="camera-grid">
        <div className="camera-view">
          <div className="camera-status">
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: coop.devices?.camera ? '#16a34a' : '#78716c' }}></span>
            <span>{coop.devices?.camera ? '🟢 Camera 1 - Trực tiếp' : '⚫ Camera 1 - Đã tắt'}</span>
          </div>
          <div className="camera-feed">
            {coop.devices?.camera ? '📹 Camera 1 hoạt động' : '📹 Camera 1 tắt'}
          </div>
        </div>
        <div className="camera-view">
          <div className="camera-status">
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: coop.devices?.camera ? '#16a34a' : '#78716c' }}></span>
            <span>{coop.devices?.camera ? '🟢 Camera 2 - Trực tiếp' : '⚫ Camera 2 - Đã tắt'}</span>
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

      <FeedingControl
        coop={coop}
        onAddFeedSchedule={onAddFeedSchedule}
        onRemoveFeedSchedule={onRemoveFeedSchedule}
        onUpdateThresholds={onUpdateThresholds}
      />

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
