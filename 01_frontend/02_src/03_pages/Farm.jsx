import { useState } from 'react';
import CoopsSearchList from '../02_components/02.2_Farm/CoopsSearchList.jsx';
import CageViewer from '../02_components/02.2_Farm/CageViewer.jsx';

export default function Farm({ coops, selectedCoop, searchQuery, onSearchChange, onSelectCoop, onBack, onToggleDevice, onAddFeed, onRemoveFeed, onUpdateThresholds, onUpdateCoop, onAddFlock, onDeleteCoop }) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newFlock, setNewFlock] = useState({ name: '', chicken_count: '', breed: '', age_weeks: '' });

  const handleAdd = () => {
    // Validate đơn giản — backend validate lại lần nữa
    if (!newFlock.name.trim() || !newFlock.chicken_count) {
      alert('Vui lòng nhập tên chuồng và số lượng gà');
      return;
    }
    onAddFlock({
      name: newFlock.name.trim(),
      chicken_count: Number(newFlock.chicken_count),
      breed: newFlock.breed.trim() || null,
      age_weeks: newFlock.age_weeks ? Number(newFlock.age_weeks) : null,
    });
    // Reset form + đóng sau khi gửi
    setNewFlock({ name: '', chicken_count: '', breed: '', age_weeks: '' });
    setShowAddForm(false);
  };

  if (selectedCoop) {
    return (
      <div className="tab-content active detail-view">
        <CageViewer
          coop={selectedCoop}
          onBack={onBack}
          onToggleDevice={onToggleDevice}
          onAddFeedSchedule={onAddFeed}
          onRemoveFeedSchedule={onRemoveFeed}
          onUpdateThresholds={onUpdateThresholds}
          onUpdateCoop={onUpdateCoop}
          onDeleteCoop={onDeleteCoop}
        />
      </div>
    );
  }

  return (
    <div className="tab-content active">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 className="section-title" style={{ fontSize: '18px', margin: 0 }}>Quản lý gà & Chuồng</h2>
        <button
          className="btn-save-finance"
          style={{ padding: '8px 16px', fontSize: '13px' }}
          onClick={() => setShowAddForm(prev => !prev)}
        >
          {showAddForm ? '✕ Hủy' : '＋ Thêm chuồng'}
        </button>
      </div>

      {showAddForm && (
        <div className="card card-default" style={{ padding: '16px', marginBottom: '12px' }}>
          <div className="form-row">
            <div className="form-group">
              <label>Tên chuồng *</label>
              <input
                type="text"
                placeholder="VD: Chuồng A4"
                value={newFlock.name}
                onChange={(e) => setNewFlock(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label>Số lượng gà *</label>
              <input
                type="number"
                placeholder="0"
                value={newFlock.chicken_count}
                onChange={(e) => setNewFlock(prev => ({ ...prev, chicken_count: e.target.value }))}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Giống</label>
              <input
                type="text"
                placeholder="VD: Lạc Dương"
                value={newFlock.breed}
                onChange={(e) => setNewFlock(prev => ({ ...prev, breed: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label>Tuổi (tuần)</label>
              <input
                type="number"
                placeholder="0"
                value={newFlock.age_weeks}
                onChange={(e) => setNewFlock(prev => ({ ...prev, age_weeks: e.target.value }))}
              />
            </div>
          </div>
          <button className="btn-save-finance" onClick={handleAdd}>💾 Lưu chuồng</button>
        </div>
      )}

      <div className="search-box">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          placeholder="Tìm kiếm chuồng..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
      <CoopsSearchList
        coops={coops}
        searchQuery={searchQuery}
        onSelectCoop={onSelectCoop}
      />
    </div>
  );
}
