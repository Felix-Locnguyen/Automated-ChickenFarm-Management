export default function DevicesList({ devices, coop, onToggleDevice, isOpen, onToggle }) {
  const deviceTypes = [
    { key: 'fan',    label: 'Quạt thông gió',  icon: '💨' },
    { key: 'light',  label: 'Đèn sưởi',        icon: '💡' },
    { key: 'camera', label: 'Camera',           icon: '📷' },
    { key: 'feeder', label: 'Máy cho ăn',       icon: '🌾' }
  ];

  return (
    <div className={`coop-device-group ${isOpen ? 'open' : ''}`}>
      <div className="coop-device-header" onClick={onToggle}>
        <span>🏠</span> {coop.name}
        <span className={`coop-device-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      {isOpen && (
        <div className="coop-device-body">
          <div className="device-grid">
            {deviceTypes.map(device => (
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

          {devices.length > 0 && (
            <div className="device-detail-list">
              {devices.map(dev => {
                const statusColor = dev.status === 'online' ? '#d1fae5' : dev.status === 'warning' ? '#fef3c7' : '#fee2e2';
                const statusTextColor = dev.status === 'online' ? '#065f46' : dev.status === 'warning' ? '#92400e' : '#7f1d1d';
                const statusEmoji = dev.status === 'online' ? '🟢' : dev.status === 'warning' ? '🟡' : '🔴';
                const statusText = dev.status === 'online' ? 'Hoạt động' : dev.status === 'warning' ? 'Cần kiểm tra' : 'Offline';
                const icon = dev.type === 'Camera' ? '📷' : dev.type === 'Sensor' ? '🌡️' : dev.type === 'Fan' ? '💨' : '🌾';

                return (
                  <div key={dev.id} className="device-card">
                    <div className="device-info">
                      <div className="device-icon">{icon}</div>
                      <div>
                        <h4 className="device-name">{dev.name}</h4>
                        <p className="device-status">{dev.type}</p>
                      </div>
                    </div>
                    <div style={{ padding: '6px 12px', borderRadius: '12px', fontSize: '11px', fontWeight: '600', backgroundColor: statusColor, color: statusTextColor }}>
                      {statusEmoji} {statusText}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
