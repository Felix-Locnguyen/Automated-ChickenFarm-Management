import { useState } from 'react';
import DevicesList from '../02_components/02.1_Dashboard/DevicesList.jsx';
import { QrShowModal, QrScanModal } from '../02_components/02.1_Dashboard/DevicePairing.jsx';

export default function Devices({ devices, coops, onToggleDevice, onPaired, onError }) {
  const [openCoopId, setOpenCoopId] = useState(null);
  const [modal, setModal] = useState(null);   // { type: 'qr', device } → hiện QR | { type: 'scan' } → quét

  const handleToggle = (coopId) => {
    setOpenCoopId(prev => prev === coopId ? null : coopId);
  };

  // Thiết bị CHƯA ghép chuồng (flockId = null) — nhóm riêng, không thì nó rơi mất
  // khỏi các nhóm theo chuồng bên dưới
  const unpaired = devices.filter(d => d.flockId == null);

  return (
    <div className="tab-content active">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 className="section-title" style={{ fontSize: '18px' }}>⚙️ Danh sách Thiết bị</h2>
        <button className="btn-cancel-modal" onClick={() => setModal({ type: 'scan' })}>
          📷 Quét QR
        </button>
      </div>

      {unpaired.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>🆕 Thiết bị chưa ghép</h3>
          {unpaired.map(dev => (
            <div
              key={dev.id}
              className="device-card"
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <h4 className="device-name">{dev.name}</h4>
                <p className="device-status">{dev.type} — chờ ghép vào chuồng</p>
              </div>
              <button className="btn-cancel-modal" onClick={() => setModal({ type: 'qr', device: dev })}>
                📱 Xem QR
              </button>
            </div>
          ))}
        </div>
      )}

      {coops.map(coop => {
        const coopDevices = devices.filter(d => d.coop === coop.name);
        return (
          <DevicesList
            key={coop.id}
            devices={coopDevices}
            coop={coop}
            onToggleDevice={onToggleDevice}
            isOpen={openCoopId === coop.id}
            onToggle={() => handleToggle(coop.id)}
          />
        );
      })}

      {modal?.type === 'qr' && (
        <QrShowModal device={modal.device} onClose={() => setModal(null)} />
      )}
      {modal?.type === 'scan' && (
        <QrScanModal
          onPaired={(device) => { setModal(null); onPaired(device); }}
          onError={onError}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}
