import { useEffect, useState } from 'react';
import { fetchLatestDetection } from '../../04_services/api';

/**
 * Hiện lần phát hiện MỚI NHẤT từ camera (polling /api/camera/latest mỗi 10s).
 *
 * - Chưa từng phát hiện → ẩn hẳn (return null).
 * - Ảnh thật + bbox vẽ theo TỶ LỆ % (lấy kích thước thật từ onLoad).
 * - Click card → modal chi tiết: ảnh + bbox + confidence từng cá thể.
 * - Lỗi mạng (backend chưa mở) → giữ dữ liệu cũ, thử lại ở lần polling sau.
 */
export default function DiseaseDetectionBox() {
  const [latest, setLatest] = useState(null);
  const [imgSize, setImgSize] = useState(null);   // {w, h} ảnh thật sau khi load
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const r = await fetchLatestDetection();
        if (alive) setLatest(r.detection || null);
      } catch {
        // backend/yolo chưa mở — bỏ qua, polling vòng sau sẽ thử lại
      }
    }
    load();
    const timer = setInterval(load, 10_000);      // polling 10s
    return () => { alive = false; clearInterval(timer); };
  }, []);

  if (!latest) return null;                       // chưa có phát hiện nào → ẩn box

  const time = latest.created_at
    ? new Date(latest.created_at).toLocaleString('vi-VN')
    : '';

  return (
    <>
      <div className="disease-box">
        <div className="disease-header">
          <span>📷</span> Camera phát hiện {latest.n_detections} cá thể ({latest.cls_name})
          <span style={{ marginLeft: 'auto', fontSize: '12px', fontWeight: 400 }}>
            conf cao nhất {latest.conf}
          </span>
        </div>
        <div
          className="disease-card"
          style={{ cursor: 'pointer' }}
          onClick={() => { setImgSize(null); setShowDetail(true); }}
        >
          <div className="disease-card-info">
            <span style={{ fontSize: '18px' }}>🐔</span>
            <div>
              <p className="disease-coop">{latest.n_detections} cá thể broiler trong khung hình</p>
              <p className="disease-time">⏰ {time}</p>
            </div>
          </div>
          <span style={{ marginLeft: 'auto', opacity: 0.6 }}>🔍</span>
        </div>
      </div>

      {showDetail && (
        <div className="modal-overlay active" onClick={() => setShowDetail(false)}>
          <div className="modal disease-detail-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">📷 Chi tiết phát hiện từ camera</h3>
              <button className="close-btn" onClick={() => setShowDetail(false)}>✕</button>
            </div>

            <div className="disease-detail-content">
              <div className="disease-detail-info">
                <span style={{ fontSize: '18px' }}>🐔</span>
                <div>
                  <p className="disease-coop">
                    {latest.n_detections} cá thể {latest.cls_name} — conf {latest.conf}
                  </p>
                  <p className="disease-time">⏰ {time}</p>
                </div>
              </div>

              {latest.img_url ? (
                <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
                  <img
                    src={latest.img_url}
                    alt="camera snapshot"
                    style={{ width: '100%', display: 'block', borderRadius: 8 }}
                    onLoad={e => setImgSize({
                      w: e.target.naturalWidth,
                      h: e.target.naturalHeight,
                    })}
                  />
                  {/* bbox overlay — vẽ theo % nên đúng mọi kích thước ảnh */}
                  {imgSize && (latest.detections || []).map((d, i) => {
                    const [x1, y1, x2, y2] = d.bbox;
                    return (
                      <div
                        key={i}
                        title={`${d.cls_name} — conf ${d.conf}`}
                        style={{
                          position: 'absolute',
                          left: `${(x1 / imgSize.w) * 100}%`,
                          top: `${(y1 / imgSize.h) * 100}%`,
                          width: `${((x2 - x1) / imgSize.w) * 100}%`,
                          height: `${((y2 - y1) / imgSize.h) * 100}%`,
                          border: '2px solid #22c55e',
                          borderRadius: 4,
                          boxShadow: '0 0 0 1px rgba(0,0,0,.45)',
                        }}
                      />
                    );
                  })}
                </div>
              ) : (
                <div className="disease-image-placeholder">
                  <span style={{ fontSize: '32px' }}>🖼️</span>
                  <p>Không lưu được ảnh</p>
                  <p>(MinIO &amp; thư mục local đều ghi lỗi)</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
