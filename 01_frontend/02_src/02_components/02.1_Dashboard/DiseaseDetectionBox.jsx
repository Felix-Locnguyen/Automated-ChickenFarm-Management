import { useState } from 'react';

const MAX_SHOW = 3;

export default function DiseaseDetectionBox({ detections }) {
  const [detailDet, setDetailDet] = useState(null);
  const [showAll, setShowAll] = useState(false);

  if (!detections || detections.length === 0) return null;

  const displayDetections = detections.slice(0, MAX_SHOW);

  return (
    <>
      <div className="disease-box">
        <div className="disease-header">
          <span>🏥</span> Phát hiện bệnh nghi ngờ
          {detections.length > MAX_SHOW && (
            <button className="disease-expand-btn" onClick={() => setShowAll(true)}>
              ☰ Xem tất cả
            </button>
          )}
        </div>
        <div className="disease-list">
          {displayDetections.map(det => (
            <div
              key={det.id}
              className="disease-card"
              onClick={() => setDetailDet(det)}
            >
              <div className="disease-card-info">
                <span style={{ fontSize: '18px' }}>🏠</span>
                <div>
                  <p className="disease-coop">{det.coopName}</p>
                  <p className="disease-time">⏰ {det.time}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {showAll && (
        <div className="modal-overlay active" onClick={() => setShowAll(false)}>
          <div className="modal disease-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">🏥 Tất cả phát hiện bệnh</h3>
              <button className="close-btn" onClick={() => setShowAll(false)}>✕</button>
            </div>
            <div className="disease-modal-list">
              {detections.map(det => (
                <div
                  key={det.id}
                  className="disease-modal-item"
                  onClick={() => { setDetailDet(det); setShowAll(false); }}
                >
                  <span style={{ fontSize: '18px' }}>🏠</span>
                  <div style={{ flex: 1 }}>
                    <p className="disease-coop">{det.coopName}</p>
                    <p className="disease-time">⏰ {det.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {detailDet && (
        <div className="modal-overlay active" onClick={() => setDetailDet(null)}>
          <div className="modal disease-detail-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">🏥 Chi tiết phát hiện bệnh</h3>
              <button className="close-btn" onClick={() => setDetailDet(null)}>✕</button>
            </div>
            <div className="disease-detail-content">
              <div className="disease-detail-info">
                <span style={{ fontSize: '18px' }}>🏠</span>
                <div>
                  <p className="disease-coop">{detailDet.coopName}</p>
                  <p className="disease-time">⏰ {detailDet.time}</p>
                </div>
              </div>
              <div className="disease-image-placeholder">
                <span style={{ fontSize: '32px' }}>🖼️</span>
                <p>Ảnh model AI</p>
                <p>(Chưa tích hợp model)</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
