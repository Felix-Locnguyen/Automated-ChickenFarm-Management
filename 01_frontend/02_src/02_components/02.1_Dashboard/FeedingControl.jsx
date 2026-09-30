import { useState } from 'react';

function getBuoi(time) {
  if (!time) return '';
  const parts = time.split(':');
  const hour = parseInt(parts[0], 10);
  return hour < 12 ? 'Sáng' : 'Chiều';
}

export default function FeedingControl({ coop, onAddFeedSchedule, onRemoveFeedSchedule, onUpdateThresholds }) {
  const [showAddFeed, setShowAddFeed] = useState(false);
  const [newFeed, setNewFeed] = useState({ hour: '6', minute: '0', second: '0' });
  const [thresholds, setThresholds] = useState(coop.thresholds || { tempMin: 20, tempMax: 35, humMin: 40, humMax: 80 });

  const handleAddFeed = () => {
    const timeStr = `${String(newFeed.hour).padStart(2, '0')}:${String(newFeed.minute).padStart(2, '0')}:${String(newFeed.second).padStart(2, '0')}`;
    onAddFeedSchedule(coop.id, { time: timeStr });
    setNewFeed({ hour: '6', minute: '0', second: '0' });
    setShowAddFeed(false);
  };

  const handleSaveThresholds = () => {
    onUpdateThresholds(coop.id, thresholds);
  };

  return (
    <>
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
                <label>Giờ</label>
                <select
                  value={newFeed.hour}
                  onChange={(e) => setNewFeed({ ...newFeed, hour: e.target.value })}
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
              <div className="feed-form-group">
                <label>Phút</label>
                <select
                  value={newFeed.minute}
                  onChange={(e) => setNewFeed({ ...newFeed, minute: e.target.value })}
                >
                  {Array.from({ length: 60 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
              <div className="feed-form-group">
                <label>Giây</label>
                <select
                  value={newFeed.second}
                  onChange={(e) => setNewFeed({ ...newFeed, second: e.target.value })}
                >
                  {Array.from({ length: 60 }, (_, i) => (
                    <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
                  ))}
                </select>
              </div>
            </div>
            <button className="btn-save-feed" onClick={handleAddFeed}>Thêm lịch</button>
          </div>
        )}

        <div className="feed-list">
          {coop.feedingSchedule && coop.feedingSchedule.length > 0 ? (
            coop.feedingSchedule
              .slice()
              .sort((a, b) => a.time.localeCompare(b.time))
              .map(schedule => (
              <div key={schedule.id} className="feed-item">
                <div className="feed-item-info">
                  <span className="feed-time">⏰ {schedule.time}</span>
                  <span className="feed-type">{getBuoi(schedule.time)}</span>
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
    </>
  );
}
