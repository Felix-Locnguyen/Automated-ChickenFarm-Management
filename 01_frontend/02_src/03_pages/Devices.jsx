import { useState } from 'react';
import DevicesList from '../02_components/02.1_Dashboard/DevicesList.jsx';

export default function Devices({ devices, coops, onToggleDevice }) {
  const [openCoopId, setOpenCoopId] = useState(null);

  const handleToggle = (coopId) => {
    setOpenCoopId(prev => prev === coopId ? null : coopId);
  };

  return (
    <div className="tab-content active">
      <h2 className="section-title" style={{ fontSize: '18px', marginBottom: '12px' }}>⚙️ Danh sách Thiết bị</h2>
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
    </div>
  );
}
