import { useState } from 'react';

export default function RecordDetailModal({ record, onClose, onEdit, onDelete, onEditSave }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});

  if (!record) return null;

  const handleStartEdit = () => {
    setEditForm({
      date: record.date,
      quantity: record.quantity,
      unitPrice: record.unitPrice,
      note: record.note || ''
    });
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    const newTotal = Number(editForm.quantity) * Number(editForm.unitPrice);
    onEditSave(record.id, record, {
      ...record,
      date: editForm.date,
      quantity: Number(editForm.quantity),
      unitPrice: Number(editForm.unitPrice),
      total: newTotal,
      note: editForm.note
    });
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditForm({});
  };

  const handleDelete = () => {
    if (confirm('Bạn có chắc muốn xóa bản ghi này?')) {
      onDelete(record.id, record);
    }
  };

  const handleChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="modal-overlay active" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">📄 Chi tiết giao dịch</h3>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div style={{ padding: '0 4px' }}>
          <div className="detail-row">
            <span className="detail-label">Loại</span>
            <span className={`fin-card-type ${record.type === 'income' ? 'type-income' : 'type-expense'}`}>
              {record.type === 'income' ? '💵 Thu' : '💸 Chi'}
            </span>
          </div>
          <div className="detail-row">
            <span className="detail-label">Nguồn</span>
            <span className="detail-value">{record.source || record.expenseType}</span>
          </div>
          {record.coopName && (
            <div className="detail-row">
              <span className="detail-label">Chuồng</span>
              <span className="detail-value">{record.coopName}</span>
            </div>
          )}

          {isEditing ? (
            <>
              <div className="detail-row">
                <span className="detail-label">Ngày</span>
                <input
                  type="date"
                  className="detail-edit-input"
                  value={editForm.date}
                  onChange={(e) => handleChange('date', e.target.value)}
                />
              </div>
              <div className="detail-row">
                <span className="detail-label">Số lượng</span>
                <input
                  type="number"
                  className="detail-edit-input"
                  value={editForm.quantity}
                  onChange={(e) => handleChange('quantity', e.target.value)}
                />
              </div>
              <div className="detail-row">
                <span className="detail-label">Đơn giá</span>
                <input
                  type="number"
                  className="detail-edit-input"
                  value={editForm.unitPrice}
                  onChange={(e) => handleChange('unitPrice', e.target.value)}
                />
              </div>
              <div className="detail-row">
                <span className="detail-label">Ghi chú</span>
                <input
                  type="text"
                  className="detail-edit-input"
                  value={editForm.note}
                  onChange={(e) => handleChange('note', e.target.value)}
                  placeholder="Ghi chú..."
                />
              </div>
              <div className="detail-row">
                <span className="detail-label">Tổng cộng</span>
                <span className="detail-value" style={{ color: record.type === 'income' ? '#16a34a' : '#dc2626', fontWeight: 700 }}>
                  {(Number(editForm.quantity) * Number(editForm.unitPrice)).toLocaleString('vi-VN')} ₫
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="detail-row">
                <span className="detail-label">Ngày</span>
                <span className="detail-value">{record.date}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Số lượng</span>
                <span className="detail-value">{record.quantity}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Đơn giá</span>
                <span className="detail-value">{record.unitPrice?.toLocaleString('vi-VN')} ₫</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Tổng cộng</span>
                <span className="detail-value" style={{ color: record.type === 'income' ? '#16a34a' : '#dc2626', fontWeight: 700 }}>
                  {record.total?.toLocaleString('vi-VN')} ₫
                </span>
              </div>
              {record.note && (
                <div className="detail-row">
                  <span className="detail-label">Ghi chú</span>
                  <span className="detail-value">{record.note}</span>
                </div>
              )}
            </>
          )}
        </div>

        {isEditing ? (
          <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
            <button className="btn-save-finance" style={{ flex: 1 }} onClick={handleSaveEdit}>💾 Thay đổi</button>
            <button className="btn-cancel-modal" style={{ flex: 1 }} onClick={handleCancelEdit}>✕ Hủy</button>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
              <button className="btn-edit" onClick={handleStartEdit}>✏️ Sửa</button>
              <button className="btn-delete-modal" onClick={handleDelete}>🗑️ Xóa</button>
            </div>
            <button className="btn-cancel-modal" style={{ width: '100%', marginTop: '8px' }} onClick={onClose}>Đóng</button>
          </>
        )}
      </div>
    </div>
  );
}
