import { useState, useEffect, useMemo } from 'react';
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

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [farmData, setFarmData] = useState({
    name: 'Trang Trại Gà Sạch Miền Tây',
    totalChickens: 12450,
    activeAlertsCount: 2,
    avgTemperature: 28.5,
    avgHumidity: 65.0,
    coops: [
      {
        id: "coop-1",
        name: "Chuồng Gà Đẻ A1",
        chickens: 4200,
        temperature: 28.2,
        humidity: 62,
        foodLevel: 85,
        waterLevel: 90,
        status: "normal",
        devices: { fan: true, light: true, camera: true, feeder: false },
        stats: { dailyEggs: "3890 quả", mortalityRate: "0.02%", feedConsumption: "420 kg" },
        feedingSchedule: [
          { id: 1, time: "06:00:00" },
          { id: 2, time: "12:00:00" },
          { id: 3, time: "18:00:00" }
        ],
        thresholds: { tempMin: 20, tempMax: 35, humMin: 40, humMax: 80 },
        logs: [
          { time: "10:30", message: "Tự động kích hoạt quạt thông gió do nhiệt độ > 28°C" },
          { time: "08:15", message: "Hoàn tất chu kỳ cho ăn buổi sáng" }
        ]
      },
      {
        id: "coop-2",
        name: "Chuồng Gà Thịt B2",
        chickens: 5050,
        temperature: 31.8,
        humidity: 78,
        foodLevel: 25,
        waterLevel: 40,
        status: "warning",
        devices: { fan: true, light: false, camera: true, feeder: true },
        stats: { avgWeight: "1.85 kg", mortalityRate: "0.05%", feedConsumption: "550 kg" },
        feedingSchedule: [
          { id: 1, time: "05:30:00" },
          { id: 2, time: "11:30:00" },
          { id: 3, time: "17:30:00" }
        ],
        thresholds: { tempMin: 18, tempMax: 32, humMin: 35, humMax: 75 },
        logs: [
          { time: "11:05", message: "⚠️ Cảnh báo: Độ ẩm vượt ngưỡng cao (78%)" },
          { time: "09:40", message: "Mức thức ăn thấp dưới 30%" }
        ]
      },
      {
        id: "coop-3",
        name: "Chuồng Gà Con C3",
        chickens: 3200,
        temperature: 26.5,
        humidity: 60,
        foodLevel: 92,
        waterLevel: 95,
        status: "normal",
        devices: { fan: false, light: true, camera: true, feeder: false },
        stats: { avgWeight: "0.45 kg", mortalityRate: "0.01%", feedConsumption: "180 kg" },
        feedingSchedule: [
          { id: 1, time: "06:00:00" },
          { id: 2, time: "14:00:00" }
        ],
        thresholds: { tempMin: 22, tempMax: 30, humMin: 50, humMax: 70 },
        logs: [{ time: "08:00", message: "Kiểm tra sức khỏe đàn gà con: Đạt tiêu chuẩn" }]
      }
    ],
    alerts: [
      { id: 1, coopName: "Chuồng Gà Thịt B2", message: "Độ ẩm cao (78%) - Đã bật quạt tăng cường", time: "11:05" },
      { id: 2, coopName: "Chuồng Gà Thịt B2", message: "Mức thức ăn thấp (25%)", time: "09:40" }
    ],
    devicesList: [
      { id: "dev-1", name: "Camera Giám Sát A1", type: "Camera", coop: "Chuồng Gà Đẻ A1", status: "online" },
      { id: "dev-2", name: "Cảm Biến Nhiệt/Ẩm A1", type: "Sensor", coop: "Chuồng Gà Đẻ A1", status: "online" },
      { id: "dev-3", name: "Hệ Thống Cho Ăn B2", type: "Feeder", coop: "Chuồng Gà Thịt B2", status: "warning" },
      { id: "dev-4", name: "Quạt Thông Gió B2", type: "Fan", coop: "Chuồng Gà Thịt B2", status: "online" },
      { id: "dev-5", name: "Camera Giám Sát C3", type: "Camera", coop: "Chuồng Gà Con C3", status: "online" }
    ],
    diseaseDetections: [
      { id: 1, coopName: "Chuồng Gà Thịt B2", time: "11:05 - 05/09/2026" },
      { id: 2, coopName: "Chuồng Gà Đẻ A1", time: "09:30 - 05/09/2026" },
      { id: 3, coopName: "Chuồng Gà Con C3", time: "08:15 - 05/09/2026" },
      { id: 4, coopName: "Chuồng Gà Thịt B2", time: "17:20 - 04/09/2026" },
      { id: 5, coopName: "Chuồng Gà Đẻ A1", time: "14:00 - 04/09/2026" },
      { id: 6, coopName: "Chuồng Gà Con C3", time: "10:45 - 03/09/2026" }
    ]
  });
  const [selectedCoopId, setSelectedCoopId] = useState(null);
  const selectedCoop = useMemo(() => {
    if (!selectedCoopId) return null;
    return farmData.coops.find(c => c.id === selectedCoopId) || null;
  }, [selectedCoopId, farmData.coops]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [financialRecords, setFinancialRecords] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setFarmData(prev => {
        const updatedCoops = prev.coops.map(coop => ({
          ...coop,
          temperature: parseFloat((coop.temperature + (Math.random() - 0.5) * 0.4).toFixed(1)),
          humidity: Math.min(100, Math.max(30, Math.round(coop.humidity + (Math.random() - 0.5))))
        }));
        const temps = updatedCoops.map(c => c.temperature);
        const hums = updatedCoops.map(c => c.humidity);
        return {
          ...prev,
          coops: updatedCoops,
          avgTemperature: parseFloat((temps.reduce((a, b) => a + b) / temps.length).toFixed(1)),
          avgHumidity: parseFloat((hums.reduce((a, b) => a + b) / hums.length).toFixed(1))
        };
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleToggleDevice = (coopId, deviceKey) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          const newState = !c.devices[deviceKey];
          const deviceNames = { fan: 'Quạt', light: 'Đèn', camera: 'Camera', feeder: 'Hệ thống ăn' };
          showToast(`Đã ${newState ? 'BẬT' : 'TẮT'} ${deviceNames[deviceKey]}`);
          return { ...c, devices: { ...c.devices, [deviceKey]: newState } };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
  };

  const handleAddFeedSchedule = (coopId, schedule) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          const newId = Math.max(0, ...c.feedingSchedule.map(s => s.id)) + 1;
          return { ...c, feedingSchedule: [...c.feedingSchedule, { ...schedule, id: newId }] };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
    showToast('Đã thêm lịch cho ăn mới');
  };

  const handleRemoveFeedSchedule = (coopId, scheduleId) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          return { ...c, feedingSchedule: c.feedingSchedule.filter(s => s.id !== scheduleId) };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
    showToast('Đã xóa lịch cho ăn');
  };

  const handleUpdateThresholds = (coopId, thresholds) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          return { ...c, thresholds };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
    showToast('Đã lưu mức cảnh báo');
  };

  const handleUpdateCoop = (coopId, name, chickens) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          return { ...c, name, chickens: Number(chickens) };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
    showToast('Đã cập nhật thông tin chuồng');
  };

  const updateCoopChickens = (coopId, newChickens) => {
    setFarmData(prev => {
      const updatedCoops = prev.coops.map(c => {
        if (c.id === coopId) {
          return { ...c, chickens: Math.max(0, newChickens) };
        }
        return c;
      });
      return { ...prev, coops: updatedCoops };
    });
  };

  const handleSaveRecord = (record) => {
    // Validate bán gà không quá số lượng có
    if (record.type === 'income' && record.source === 'Bán gà') {
      const coop = farmData.coops.find(c => c.id === record.coopId);
      if (coop && record.quantity > coop.chickens) {
        showToast('Số lượng bán vượt quá gà hiện có trong chuồng');
        return;
      }
      if (coop) {
        updateCoopChickens(record.coopId, coop.chickens - record.quantity);
      }
    }

    // Gà chết → trừ gà
    if (record.type === 'expense' && record.expenseType === 'Gà chết') {
      const coop = farmData.coops.find(c => c.id === record.coopId);
      if (coop) {
        updateCoopChickens(record.coopId, coop.chickens - record.quantity);
      }
    }

    setFinancialRecords(prev => [...prev, { ...record, id: Date.now(), createdAt: new Date().toISOString() }]);
    showToast('Đã lưu bản ghi');
  };

  const handleEditRecord = (id, oldRecord, newData) => {
    // Bán gà → cập nhật lại số gà
    if (newData.type === 'income' && newData.source === 'Bán gà') {
      const coop = farmData.coops.find(c => c.id === newData.coopId);
      if (coop) {
        const newChickens = coop.chickens + oldRecord.quantity - newData.quantity;
        if (newChickens < 0) {
          showToast('Số lượng bán vượt quá gà hiện có trong chuồng');
          return;
        }
        updateCoopChickens(newData.coopId, newChickens);
      }
    }

    // Gà chết → cập nhật lại số gà
    if (newData.type === 'expense' && newData.expenseType === 'Gà chết') {
      const coop = farmData.coops.find(c => c.id === newData.coopId);
      if (coop) {
        const newChickens = coop.chickens + oldRecord.quantity - newData.quantity;
        if (newChickens < 0) {
          showToast('Số lượng không hợp lệ');
          return;
        }
        updateCoopChickens(newData.coopId, newChickens);
      }
    }

    setFinancialRecords(prev => prev.map(r => r.id === id ? { ...r, ...newData } : r));
    showToast('Đã cập nhật bản ghi');
  };

  const handleDeleteRecord = (id, record) => {
    // Bán gà → khôi phục gà đã bán
    if (record.type === 'income' && record.source === 'Bán gà') {
      const coop = farmData.coops.find(c => c.id === record.coopId);
      if (coop) {
        updateCoopChickens(record.coopId, coop.chickens + record.quantity);
      }
    }

    // Gà chết → khôi phục gà đã chết
    if (record.type === 'expense' && record.expenseType === 'Gà chết') {
      const coop = farmData.coops.find(c => c.id === record.coopId);
      if (coop) {
        updateCoopChickens(record.coopId, coop.chickens + record.quantity);
      }
    }

    setFinancialRecords(prev => prev.filter(r => r.id !== id));
    showToast('Đã xóa bản ghi');
  };

  const switchTab = (tabName) => {
    setActiveTab(tabName);
    if (tabName !== 'coopsTab') {
      setSelectedCoopId(null);
    }
  };

  const showCoopDetail = (coop) => {
    setSelectedCoopId(coop.id);
    setActiveTab('coopsTab');
  };

  const backToDashboard = () => {
    setSelectedCoopId(null);
    setActiveTab('dashboard');
  };

  const handleLogin = (user) => {
    setCurrentUser(user);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setIsLoggedIn(false);
    setActiveTab('dashboard');
    setSelectedCoopId(null);
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="container">
      <AlertNotification message={toastMessage} />

      <header>
        <div className="header-left">
          <span className="emoji-icon">🚜</span>
          <div>
            <h1>Quản Lý Trang Trại Gà</h1>
            <p>{farmData.name}</p>
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
            coops={farmData.coops}
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
            coops={farmData.coops}
            records={financialRecords}
            onSaveRecord={handleSaveRecord}
            onEditRecord={handleEditRecord}
            onDeleteRecord={handleDeleteRecord}
          />
        )}

        {activeTab === 'financeManagementTab' && (
          <FinanceManagementTab records={financialRecords} />
        )}

        {activeTab === 'devicesTab' && !selectedCoop && (
          <Devices devices={farmData.devicesList} coops={farmData.coops} onToggleDevice={handleToggleDevice} />
        )}
      </main>

      {showAlertModal && (
        <AlertPanel
          alerts={farmData.alerts}
          activeAlertsCount={farmData.activeAlertsCount}
          show={showAlertModal}
          onClose={() => setShowAlertModal(false)}
        />
      )}

      <Navbar activeTab={activeTab} onSwitchTab={switchTab} />
    </div>
  );
}
