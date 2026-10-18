import { useState, useEffect, useMemo, useCallback } from 'react';
import './App.css';

import LoginPage from './03_pages/LoginPage.jsx';
import Dashboard from './03_pages/Dashboard.jsx';
import Farm from './03_pages/Farm.jsx';
import FinancialTab from './02_components/02.3_Financial/FinancialTab.jsx';
import FinanceManagementTab from './02_components/02.4_FinanceManagement/FinanceManagementTab.jsx';
import Devices from './03_pages/Devices.jsx';

import AlertPanel from './02_components/02.1_Dashboard/AlertPanel.jsx';
import Navbar from './02_components/02.4_Common/Navbar.jsx';
import AlertNotification from './02_components/02.4_Common/AlertNotification.jsx';

import { isLoggedIn as checkLoggedIn, logout } from './04_services/auth';
import {
  fetchFlocks,
  updateFlock,
  fetchDevices,
  toggleDevice,
  fetchAlerts,
  fetchLatestReading,
  fetchFeedingLogs,
  createFeedingLog,
  deleteFeedingLog,
  fetchFinancialRecords,
  createFinancialRecord,
  updateFinancialRecord,
  deleteFinancialRecord,
} from './04_services/api';

/* ============================================================
 *  ADAPTER LAYER — chuyển "shape backend" → "shape UI"
 *
 *  Backend lưu theo mô hình DB (chicken_count, flock_id, is_active...)
 *  còn các component (CoopsList, AlertPanel, DevicesList...) được viết
 *  từ trước expecting shape khác (chickens, coopName, devices.fan...).
 *
 *  Thay vì sửa 20+ component, ta có 1 lớp hàm mapping ở đây:
 *  backend đổi tên trường → chỉ sửa adapter, UI không động tới.
 * ============================================================ */

/** Flock (DB) → coop object mà CoopsList / CageViewer / DevicesList cần. */
function flockToCoop(flock, reading, devices, feedingLogs, alerts, thresholdsMap) {
  const coopDevices = devices.filter(d => d.flock_id === flock.id);
  const hasAlert = alerts.some(a => a.flock_id === flock.id);

  // Device.toggle trong UI: 4 công tắc boolean — derive từ is_active của thiết bị thật
  const isOn = (type) => coopDevices.some(d => d.type === type && d.is_active);

  return {
    id: flock.id,
    name: flock.name,
    chickens: flock.chicken_count,
    // TODO Phase 2: cảm biến theo từng chuồng (mỗi device 1 flock)
    // → tạm thời dùng reading mới nhất chung cho mọi chuồng
    temperature: reading?.temperature ?? '--',
    humidity: reading?.humidity ?? '--',
    foodLevel: reading?.food_level ?? 0,
    waterLevel: reading?.water_level ?? 0,
    status: hasAlert ? 'warning' : 'normal',
    devices: {
      fan: isOn('fan'),
      light: isOn('light'),
      camera: isOn('camera'),
      feeder: isOn('feeder'),
    },
    stats: {},            // CageViewer hiển thị — backend chưa có (Phase 2)
    feedingSchedule: feedingLogs
      .filter(l => l.flock_id === flock.id && l.status === 'pending')
      .map(l => ({ id: l.id, time: l.scheduled_time })),
    thresholds: thresholdsMap[flock.id] || { tempMin: 20, tempMax: 35, humMin: 40, humMax: 80 },
    logs: [],
  };
}

/** Alert (DB) → alert mà AlertPanel hiển thị. */
function alertToUi(alert) {
  return {
    id: alert.id,
    coopName: alert.coop_name || 'Hệ thống',   // backend đã nối tên chuồng sẵn
    message: alert.message,
    time: alert.created_at
      ? new Date(alert.created_at).toLocaleString('vi-VN', {
          hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit',
        })
      : '',
    flockId: alert.flock_id,
  };
}

/** Device (DB) → device mà DevicesList hiển thị (type viết hoa, coop = TÊN chuồng). */
function deviceToUi(device, flocks) {
  return {
    id: device.id,
    name: device.name,
    // 'fan' → 'Fan' (DevicesList so sánh 'Fan' | 'Camera' | 'Sensor')
    type: device.type.charAt(0).toUpperCase() + device.type.slice(1),
    coop: flocks.find(f => f.id === device.flock_id)?.name || 'Chưa gán chuồng',
    status: device.status,
    flockId: device.flock_id,
    rawType: device.type,
    isActive: device.is_active,
  };
}

/** FinancialRecord (DB) → record mà RecentRecords / RecordDetailModal hiển thị. */
function recordToUi(r, flocks) {
  const coopName = flocks.find(f => f.id === r.flock_id)?.name || 'Nhiều chuồng';
  const base = {
    id: r.id,
    coopId: r.flock_id,
    coopName,
    date: (r.date || '').split('T')[0],   // '2026-10-18T...' → '2026-10-18'
    note: r.note,
  };
  if (r.category === 'ban_ga') {
    return { ...base, type: 'income', source: 'Bán gà', quantity: r.sold_chickens, unitPrice: r.unit_price, total: r.revenue };
  }
  if (r.category === 'ban_trung') {
    return { ...base, type: 'income', source: 'Bán trứng', quantity: r.sold_chickens, unitPrice: r.unit_price, total: r.revenue };
  }
  if (r.category === 'ga_chet') {
    return { ...base, type: 'expense', expenseType: 'Gà chết', quantity: r.dead_chickens, unitPrice: r.cost_per_chick, total: r.depreciation_cost };
  }
  // thuc_an: backend chỉ lưu tổng tiền feed_cost → hiển thị quantity=1
  const feedTotal = (r.feed_cost || 0) + (r.other_cost || 0);
  return { ...base, type: 'expense', expenseType: 'Thức ăn/Thuốc', quantity: 1, unitPrice: feedTotal, total: feedTotal };
}

/** Record từ UI form → payload POST/PUT /financial (backend tự tính revenue/profit). */
function recordToApiPayload(record, coops) {
  const coop = coops.find(c => c.id === record.coopId);
  const base = {
    flock_id: record.coopId ?? null,
    date: record.date ? `${record.date}T00:00:00` : new Date().toISOString(),
    quantity_before: coop?.chickens ?? 0,
    note: record.note || null,
  };

  if (record.type === 'income' && record.source === 'Bán gà') {
    return { ...base, category: 'ban_ga', sold_chickens: record.quantity, unit_price: record.unitPrice };
  }
  if (record.type === 'income') {  // Bán trứng — dùng chung trường sold_chickens để backend tính revenue
    return { ...base, category: 'ban_trung', sold_chickens: record.quantity, unit_price: record.unitPrice };
  }
  if (record.expenseType === 'Gà chết') {
    return { ...base, category: 'ga_chet', dead_chickens: record.quantity, cost_per_chick: record.unitPrice };
  }
  // Thức ăn / Thuốc: chỉ lưu tổng tiền
  return { ...base, category: 'thuc_an', feed_cost: record.total, other_cost: 0 };
}

/** Cập nhật số gà trong DB — gửi ĐỦ field vì PUT /flocks ghi đè toàn bộ record. */
function buildFlockPayload(flock, chickenCount) {
  return {
    name: flock.name,
    chicken_count: Math.max(0, chickenCount),
    breed: flock.breed,
    age_weeks: flock.age_weeks,
    coop_number: flock.coop_number,
  };
}


export default function App() {
  // ===== Trạng thái đăng nhập =====
  // checkLoggedIn() đọc localStorage → giữ đăng nhập sau F5
  const [isLoggedIn, setIsLoggedIn] = useState(checkLoggedIn);
  const [currentUser, setCurrentUser] = useState(() => localStorage.getItem('userEmail'));

  // ===== Dữ liệu THẬT từ backend =====
  const [flocks, setFlocks] = useState([]);
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);           // alerts CHƯA xử lý
  const [latestReading, setLatestReading] = useState(null);
  const [feedingLogs, setFeedingLogs] = useState([]);
  const [financialRecords, setFinancialRecords] = useState([]);

  // Ngưỡng cảnh báo theo chuồng — tạm lưu local, Phase 2 sẽ có bảng trong DB
  const [thresholdsMap, setThresholdsMap] = useState({});

  // ===== Trạng thái UI =====
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedCoopId, setSelectedCoopId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  /** Tải lại TOÀN BỘ dữ liệu — gọi sau mỗi thao tác CRUD cho dữ liệu luôn nhất quán. */
  const loadData = useCallback(async () => {
    try {
      setLoadError(null);
      const [flocksData, devicesData, alertsData, logsData, recordsData] = await Promise.all([
        fetchFlocks(),
        fetchDevices(),
        fetchAlerts(),          // ?resolved=false → chỉ cảnh báo chưa xử lý
        fetchFeedingLogs(),     // tải 1 lần, group theo flock_id ở adapter
        fetchFinancialRecords(),
      ]);
      setFlocks(flocksData);
      setDevices(devicesData);
      setAlerts(alertsData);
      setFeedingLogs(logsData);
      setFinancialRecords(recordsData);

      // reading cuối cùng — không chặn màn hình chính nếu chưa có dữ liệu cảm biến
      const reading = await fetchLatestReading().catch(() => null);
      setLatestReading(reading);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Tải dữ liệu khi đã đăng nhập (kể cả F5 — token còn trong localStorage)
  useEffect(() => {
    if (isLoggedIn) loadData();
  }, [isLoggedIn, loadData]);

  // Poll cảm biến + cảnh báo mỗi 10s (thay cho random interval giả lập cũ)
  useEffect(() => {
    if (!isLoggedIn) return;
    const timer = setInterval(async () => {
      try {
        const [reading, alertsData] = await Promise.all([fetchLatestReading(), fetchAlerts()]);
        setLatestReading(reading);
        setAlerts(alertsData);
      } catch {
        // mạng chập chờn ở poll thì bỏ qua — thao tác chính sẽ báo lỗi riêng
      }
    }, 10000);
    return () => clearInterval(timer);
  }, [isLoggedIn]);

  // ===== ADAPTER: dữ liệu backend → dữ liệu cho từng tab =====
  const coops = useMemo(
    () => flocks.map(f => flockToCoop(f, latestReading, devices, feedingLogs, alerts, thresholdsMap)),
    [flocks, latestReading, devices, feedingLogs, alerts, thresholdsMap],
  );
  const uiAlerts = useMemo(() => alerts.map(alertToUi), [alerts]);
  const uiDevices = useMemo(() => devices.map(d => deviceToUi(d, flocks)), [devices, flocks]);
  const uiRecords = useMemo(
    () => financialRecords.map(r => recordToUi(r, flocks)),
    [financialRecords, flocks],
  );
  const selectedCoop = useMemo(
    () => coops.find(c => c.id === selectedCoopId) || null,
    [coops, selectedCoopId],
  );

  // "shape cũ" mà Dashboard/Farm/Devices đang expect — dựng từ data thật
  const farmData = useMemo(() => ({
    name: 'Trang Trại Gà Thông Minh',
    coops,
    alerts: uiAlerts,
    activeAlertsCount: uiAlerts.length,
    avgTemperature: latestReading?.temperature ?? '--',
    avgHumidity: latestReading?.humidity ?? '--',
    devicesList: uiDevices,
    diseaseDetections: [],   // TODO Phase 3 — AI nhận diện bệnh
  }), [coops, uiAlerts, uiDevices, latestReading]);

  // ===== XỬ LÝ THAO TÁC =====

  /** Bật/tắt thiết bị → PUT /devices/{id}/toggle, cập nhật state từ kết quả server trả về. */
  const handleToggleDevice = async (coopId, deviceKey) => {
    const device = devices.find(d => d.flock_id === coopId && d.type === deviceKey);
    if (!device) {
      showToast(`Chuồng này chưa có thiết bị ${deviceKey} — thêm ở Phase 2 (ghép QR)`);
      return;
    }
    try {
      const updated = await toggleDevice(device.id);   // server trả về device ĐÃ đảo trạng thái
      setDevices(prev => prev.map(d => (d.id === updated.id ? updated : d)));
      showToast(`Đã ${updated.is_active ? 'BẬT' : 'TẮT'} ${device.name}`);
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /** Thêm lịch cho ăn → POST /feeding (lưu DB, không mất sau F5). */
  const handleAddFeedSchedule = async (coopId, schedule) => {
    try {
      await createFeedingLog({
        flock_id: Number(coopId),
        feed_type: 'Tự động',
        amount_kg: 0,                       // TODO: form nhập kg (Phase 2)
        scheduled_time: schedule.time,      // '06:00:00'
      });
      setFeedingLogs(await fetchFeedingLogs());
      showToast('Đã thêm lịch cho ăn');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /** Xóa lịch cho ăn → DELETE /feeding/{id}. */
  const handleRemoveFeedSchedule = async (coopId, scheduleId) => {
    try {
      await deleteFeedingLog(scheduleId);
      setFeedingLogs(await fetchFeedingLogs());
      showToast('Đã xóa lịch cho ăn');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /** Lưu ngưỡng cảnh báo — tạm local, Phase 2 tạo bảng thresholds + PUT. */
  const handleUpdateThresholds = (coopId, thresholds) => {
    setThresholdsMap(prev => ({ ...prev, [coopId]: thresholds }));
    showToast('Đã lưu mức cảnh báo (chưa lưu server — Phase 2)');
  };

  /** Sửa tên / số gà chuồng → PUT /flocks/{id}. */
  const handleUpdateCoop = async (coopId, name, chickens) => {
    const flock = flocks.find(f => f.id === coopId);
    if (!flock) return;
    try {
      await updateFlock(coopId, buildFlockPayload(flock, Number(chickens)));
      setFlocks(prev => prev.map(f => (f.id === coopId
        ? { ...f, name, chicken_count: Number(chickens) }
        : f)));
      showToast('Đã cập nhật thông tin chuồng');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /** Trừ/cong số gà khi tạo/sửa/xóa phiếu bán gà hoặc gà chết. */
  const adjustChickenCount = async (coopId, delta) => {
    const flock = flocks.find(f => f.id === coopId);
    if (!flock) return;
    await updateFlock(coopId, buildFlockPayload(flock, flock.chicken_count + delta));
    setFlocks(prev => prev.map(f => (f.id === coopId
      ? { ...f, chicken_count: Math.max(0, f.chicken_count + delta) }
      : f)));
  };

  /** Lưu phiếu thu/chi mới → POST /financial + trừ gà nếu cần. */
  const handleSaveRecord = async (record) => {
    const changesFlock = (record.type === 'income' && record.source === 'Bán gà')
      || (record.type === 'expense' && record.expenseType === 'Gà chết');
    try {
      await createFinancialRecord(recordToApiPayload(record, coops));
      if (changesFlock && record.coopId) {
        await adjustChickenCount(record.coopId, -record.quantity);
      }
      setFinancialRecords(await fetchFinancialRecords());
      showToast('Đã lưu phiếu trên server');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /**
   * Sửa phiếu → PUT /financial/{id}.
   * Ghi chú: RecordDetailModal gọi onEditSave(id, oldRecord, newData),
   * còn đường "Sửa nhanh" chỉ gửi 2 đối số → bỏ qua (form chưa hỗ trợ prefill).
   */
  const handleEditRecord = async (id, oldRecord, newData) => {
    if (!newData) return;
    const changesFlock = (newData.type === 'income' && newData.source === 'Bán gà')
      || (newData.type === 'expense' && newData.expenseType === 'Gà chết');
    try {
      await updateFinancialRecord(id, recordToApiPayload(newData, coops));
      if (changesFlock && newData.coopId) {
        // chickens cũ − chickens mới = phần được "hoàn" lại đàn
        await adjustChickenCount(newData.coopId, oldRecord.quantity - newData.quantity);
      }
      setFinancialRecords(await fetchFinancialRecords());
      showToast('Đã cập nhật bản ghi');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  /** Xóa phiếu → DELETE + hoàn lại số gà. */
  const handleDeleteRecord = async (id, record) => {
    const changesFlock = (record.type === 'income' && record.source === 'Bán gà')
      || (record.type === 'expense' && record.expenseType === 'Gà chết');
    try {
      await deleteFinancialRecord(id);
      if (changesFlock && record.coopId) {
        await adjustChickenCount(record.coopId, record.quantity);
      }
      setFinancialRecords(await fetchFinancialRecords());
      showToast('Đã xóa bản ghi');
    } catch (err) {
      showToast(`Lỗi: ${err.message}`);
    }
  };

  // ===== Điều hướng =====
  const switchTab = (tabName) => {
    setActiveTab(tabName);
    if (tabName !== 'coopsTab') setSelectedCoopId(null);
  };

  const showCoopDetail = (coop) => {
    setSelectedCoopId(coop.id);
    setActiveTab('coopsTab');
  };

  const backToDashboard = () => {
    setSelectedCoopId(null);
    setActiveTab('dashboard');
  };

  // ===== Đăng nhập / đăng xuất =====
  const handleLogin = (user) => {
    setCurrentUser(user.email);
    setIsLoggedIn(true);
    loadData();                    // token đã lưu → tải dữ liệu ngay
  };

  const handleLogout = () => {
    logout();                      // xóa token khỏi localStorage
    setIsLoggedIn(false);
    setCurrentUser(null);
    setActiveTab('dashboard');
    setSelectedCoopId(null);
    // reset dữ liệu để user sau không thấy data của user trước
    setFlocks([]); setDevices([]); setAlerts([]);
    setFeedingLogs([]); setFinancialRecords([]); setLatestReading(null);
  };

  // ===== RENDER =====
  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <h2>⏳ Đang tải dữ liệu trang trại...</h2>
      </div>
    );
  }

  return (
    <div className="container">
      <AlertNotification message={toastMessage} />

      <header>
        <div className="header-left">
          <span className="emoji-icon">🚜</span>
          <div>
            <h1>Quản Lý Trang Trại Gà</h1>
            <p>{farmData.name}{currentUser ? ` — ${currentUser}` : ''}</p>
          </div>
        </div>
        <div className="header-right">
          <button className="btn-icon" onClick={() => setShowAlertModal(true)}>
            🔔
            {farmData.activeAlertsCount > 0 && (
              <span className="alert-badge">{farmData.activeAlertsCount}</span>
            )}
          </button>
          <button className="btn-logout" onClick={handleLogout} title="Đăng xuất">
            🚪
          </button>
        </div>
      </header>

      {loadError && (
        <div style={{
          backgroundColor: '#fee2e2', color: '#7f1d1d', padding: '10px 16px',
          borderRadius: '8px', marginBottom: '12px', fontSize: '13px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>⚠️ Không tải được dữ liệu: {loadError}</span>
          <button onClick={loadData} style={{
            border: 'none', backgroundColor: '#7f1d1d', color: '#fff',
            padding: '4px 12px', borderRadius: '6px', cursor: 'pointer',
          }}>
            Thử lại
          </button>
        </div>
      )}

      <main>
        {activeTab === 'dashboard' && !selectedCoop && (
          <Dashboard
            farmData={farmData}
            onSelectCoop={showCoopDetail}
            showAlertModal={showAlertModal}
            onShowAlert={() => setShowAlertModal(true)}
            onCloseAlert={() => setShowAlertModal(false)}
          />
        )}

        {activeTab === 'coopsTab' && (
          <Farm
            coops={coops}
            selectedCoop={selectedCoop}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSelectCoop={showCoopDetail}
            onBack={backToDashboard}
            onToggleDevice={handleToggleDevice}
            onAddFeed={handleAddFeedSchedule}
            onRemoveFeed={handleRemoveFeedSchedule}
            onUpdateThresholds={handleUpdateThresholds}
            onUpdateCoop={handleUpdateCoop}
          />
        )}

        {activeTab === 'financialTab' && (
          <FinancialTab
            coops={coops}
            records={uiRecords}
            onSaveRecord={handleSaveRecord}
            onEditRecord={handleEditRecord}
            onDeleteRecord={handleDeleteRecord}
          />
        )}

        {activeTab === 'financeManagementTab' && (
          <FinanceManagementTab records={uiRecords} />
        )}

        {activeTab === 'devicesTab' && !selectedCoop && (
          <Devices devices={uiDevices} coops={coops} onToggleDevice={handleToggleDevice} />
        )}
      </main>

      {showAlertModal && (
        <AlertPanel
          alerts={uiAlerts}
          activeAlertsCount={farmData.activeAlertsCount}
          show={showAlertModal}
          onClose={() => setShowAlertModal(false)}
        />
      )}

      <Navbar activeTab={activeTab} onSwitchTab={switchTab} />
    </div>
  );
}
