/**
 * B8 — Ghép thiết bị bằng QR:
 *  - QrShowModal: hiển thị mã QR của 1 thiết bị (data-URI backend trả về, không cần server ảnh)
 *                  + code 6 ký tự để copy/dán tay.
 *  - QrScanModal: quét QR bằng camera (jsQR + getUserMedia), hoặc nhập code tay nếu
 *                  camera bị từ chối / máy tính không có camera.
 */
import { useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';
import { getDeviceQr, pairDevice } from '../../04_services/api';

/** Hiển thị mã QR — dán lên thiết bị, ai quét (hoặc mở link) sẽ ghép vào chuồng của họ. */
export function QrShowModal({ device, onClose }) {
  const [qr, setQr] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    getDeviceQr(device.id)
      .then(data => alive && setQr(data))
      .catch(err => alive && setError(err.message));
    return () => { alive = false; };
  }, [device.id]);

  return (
    <div className="modal-overlay active" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ textAlign: 'center' }}>
        <div className="modal-header">
          <h3 className="modal-title">📱 Mã ghép — {device.name}</h3>
          <button className="btn-cancel-modal" onClick={onClose}>✕</button>
        </div>

        {error && <p style={{ color: '#7f1d1d' }}>Lỗi: {error}</p>}
        {!error && !qr && <p>Đang tạo mã QR...</p>}

        {qr && (
          <>
            <img src={qr.qr_image} alt="Mã QR ghép thiết bị" style={{ width: 220, height: 220 }} />
            <p style={{ fontSize: '26px', fontWeight: 700, letterSpacing: '6px', margin: '8px 0' }}>
              {qr.pairing_code}
            </p>
            <p style={{ fontSize: '12px', color: '#6b7280', wordBreak: 'break-all' }}>
              Quét mã này bằng điện thoại (hoặc mở link) để ghép thiết bị vào chuồng của bạn.
              <br />{qr.pair_url}
            </p>
          </>
        )}
      </div>
    </div>
  );
}

/** Quét QR bằng camera → POST /devices/pair. Không có camera → nhập mã 6 ký tự tay. */
export function QrScanModal({ onPaired, onError, onClose }) {
  const videoRef = useRef(null);
  const busyRef = useRef(false);          // chặn quét liên tục bắn nhiều request cùng lúc
  const [manualCode, setManualCode] = useState('');
  const [busy, setBusy] = useState(false);

  const handlePair = async (code) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    try {
      const device = await pairDevice(code.trim().toUpperCase());
      onPaired(device);                   // App: tải lại dữ liệu + toast; modal tự đóng
    } catch (err) {
      onError(err.message);               // "Không tồn tại hoặc bạn không có quyền" / "đã được ghép"...
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  // Camera + vòng quét jsQR — dọn sạch khi đóng modal (StrictMode dev: mount→unmount→mount vẫn OK)
  useEffect(() => {
    let stream = null;
    let raf = 0;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');

    const tick = () => {
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const found = jsQR(img.data, img.width, img.height);
        if (found?.data) {
          const m = found.data.match(/[?&]token=([A-Za-z0-9]+)/);   // QR chứa link ?token=XXX
          const code = m ? m[1] : found.data.trim();               // hoặc in thẳng mã 6 ký tự
          if (code) {
            handlePair(code);             // dừng quét — ghép xong parent đóng modal,
            return;                       // ghép lỗi thì dùng ô nhập tay bên dưới
          }
        }
      }
      raf = requestAnimationFrame(tick);
    };

    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: 'environment' } })     // camera sau nếu là điện thoại
      .then(s => {
        stream = s;
        video.srcObject = s;
        video.play().then(() => { raf = requestAnimationFrame(tick); });
      })
      .catch(() => { /* camera bị từ chối → im lặng, chỉ dùng nhập code tay */ });

    return () => {
      cancelAnimationFrame(raf);
      stream?.getTracks().forEach(t => t.stop());   // TẮT camera khi đóng modal
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="modal-overlay active" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">📷 Quét mã QR ghép thiết bị</h3>
          <button className="btn-cancel-modal" onClick={onClose}>✕</button>
        </div>

        <video
          ref={videoRef}
          muted
          playsInline
          style={{ width: '100%', borderRadius: 12, background: '#000', minHeight: '160px' }}
        />
        <p style={{ fontSize: '12px', color: '#6b7280', margin: '8px 0' }}>
          Hướng camera vào mã QR trên thiết bị. Không có camera? Nhập mã 6 ký tự bên dưới.
        </p>

        <div style={{ display: 'flex', gap: 8 }}>
          <input
            value={manualCode}
            onChange={e => setManualCode(e.target.value.toUpperCase())}
            maxLength={6}
            placeholder="VD: XK5R7B"
            style={{
              flex: 1, padding: '8px 12px', borderRadius: 8,
              border: '1px solid #d4a574', letterSpacing: '3px', textTransform: 'uppercase',
            }}
          />
          <button
            className="btn-cancel-modal"
            disabled={manualCode.length !== 6 || busy}
            style={{ opacity: manualCode.length !== 6 || busy ? 0.5 : 1 }}
            onClick={() => handlePair(manualCode)}
          >
            {busy ? 'Đang ghép...' : 'Ghép'}
          </button>
        </div>
      </div>
    </div>
  );
}
