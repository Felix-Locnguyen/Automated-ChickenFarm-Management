import { useState } from 'react';

export default function IncomeForm({ coops, onSave }) {
  const [form, setForm] = useState({
    coopId: '',
    date: new Date().toISOString().split('T')[0],
    source: 'ban_ga',
    quantity: '',
    unitPrice: '',
    note: ''
  });

  const total = (Number(form.quantity) || 0) * (Number(form.unitPrice) || 0);

  const handleChange = (field, value) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    if (!form.coopId || !form.quantity || !form.unitPrice) {
      alert('Vui lòng điền đầy đủ thông tin');
      return;
    }

    // Validate bán gà không quá số lượng có
    if (form.source === 'ban_ga') {
      const coop = coops.find(c => c.id === form.coopId);
      if (coop && Number(form.quantity) > coop.chickens) {
        alert(`Số lượng bán (${form.quantity}) vượt quá gà hiện có (${coop.chickens}) trong chuồng`);
        return;
      }
    }

    onSave({
      type: 'income',
      coopId: form.coopId,
      coopName: coops.find(c => c.id === form.coopId)?.name || '',
      date: form.date,
      source: form.source === 'ban_ga' ? 'Bán gà' : 'Bán trứng',
      quantity: Number(form.quantity),
      unitPrice: Number(form.unitPrice),
      total,
      note: form.note
    });
    setForm({ coopId: '', date: new Date().toISOString().split('T')[0], source: 'ban_ga', quantity: '', unitPrice: '', note: '' });
  };

  return (
    <div className="card card-default" style={{ padding: '16px', marginBottom: '16px' }}>
      <div className="form-row">
        <div className="form-group">
          <label>Chuồng</label>
          <select value={form.coopId} onChange={(e) => handleChange('coopId', e.target.value)}>
            <option value="">-- Chọn chuồng --</option>
            {coops.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Ngày</label>
          <input type="date" value={form.date} onChange={(e) => handleChange('date', e.target.value)} />
        </div>
      </div>

      <div className="form-group" style={{ marginBottom: '12px' }}>
        <label>Nguồn thu</label>
        <select value={form.source} onChange={(e) => handleChange('source', e.target.value)}>
          <option value="ban_ga">Bán gà</option>
          <option value="ban_trung">Bán trứng</option>
        </select>
      </div>

      {form.source === 'ban_ga' && form.coopId && (
        <div style={{ fontSize: '12px', color: '#a0826d', marginBottom: '12px', padding: '8px', backgroundColor: '#f5ede0', borderRadius: '6px' }}>
          🐔 Gà hiện có trong chuồng: <b style={{ color: '#654321' }}>
            {coops.find(c => c.id === form.coopId)?.chickens?.toLocaleString('vi-VN') || 0} con
          </b>
        </div>
      )}

      <div className="form-row">
        <div className="form-group">
          <label>Số lượng</label>
          <input type="number" placeholder="0" value={form.quantity} onChange={(e) => handleChange('quantity', e.target.value)} />
        </div>
        <div className="form-group">
          <label>Đơn giá</label>
          <input type="number" placeholder="0" value={form.unitPrice} onChange={(e) => handleChange('unitPrice', e.target.value)} />
        </div>
      </div>

      <div className="form-group" style={{ marginBottom: '12px' }}>
        <label>Ghi chú</label>
        <input type="text" placeholder="Ghi chú..." value={form.note} onChange={(e) => handleChange('note', e.target.value)} />
      </div>

      <div className="total-display">
        <p className="total-label">Tổng thu</p>
        <p className="total-value">{total.toLocaleString('vi-VN')} ₫</p>
      </div>

      <button className="btn-save-finance" onClick={handleSave}>Lưu phiếu thu</button>
    </div>
  );
}
