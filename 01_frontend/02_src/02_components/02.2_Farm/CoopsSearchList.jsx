export default function CoopsSearchList({ coops, searchQuery, onSelectCoop }) {
  const filtered = coops.filter(c => c.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div>
      {filtered.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '14px', paddingTop: '20px' }}>
          {coops.length === 0 ? 'Chưa có dữ liệu chuồng' : 'Không tìm thấy chuồng'}
        </p>
      ) : (
        filtered.map(coop => (
          <div
            key={coop.id}
            className="coop-card"
            onClick={() => onSelectCoop(coop)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          >
            <div style={{ display: 'flex', gap: '12px', alignItems: 'start', flex: 1 }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '8px',
                backgroundColor: '#fef3c7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px'
              }}>
                🐔
              </div>
              <div>
                <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#654321', margin: 0 }}>{coop.name}</h4>
                <p style={{ fontSize: '12px', color: '#a0826d', margin: '4px 0 0 0' }}>Số lượng: {coop.chickens.toLocaleString('vi-VN')} con</p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', backgroundColor: '#e8d9ca', color: '#654321', padding: '2px 6px', borderRadius: '4px', fontWeight: '600' }}>
                    🌡️ {coop.temperature}°C
                  </span>
                  <span style={{ fontSize: '11px', backgroundColor: '#e8d9ca', color: '#654321', padding: '2px 6px', borderRadius: '4px', fontWeight: '600' }}>
                    💧 {coop.humidity}%
                  </span>
                </div>
              </div>
            </div>
            <span style={{ fontSize: '18px' }}>→</span>
          </div>
        ))
      )}
    </div>
  );
}
