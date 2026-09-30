export default function RecentRecords({ records, onViewDetail }) {
  const recent = records.slice(-5).reverse();

  if (recent.length === 0) {
    return (
      <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '13px', padding: '16px 0' }}>
        Chưa có dữ liệu
      </p>
    );
  }

  return (
    <div>
      {recent.map(rec => (
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
            <span>📦 <b>{rec.quantity}</b></span>
            <span>💰 <b>{rec.unitPrice?.toLocaleString('vi-VN')}</b></span>
          </div>
        </div>
      ))}
    </div>
  );
}
