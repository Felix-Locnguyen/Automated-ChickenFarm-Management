export default function Navbar({ activeTab, onSwitchTab }) {
  return (
    <nav>
      <button
        className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
        onClick={() => onSwitchTab('dashboard')}
      >
        <div className="nav-icon">🏠</div>
        <span>Trang chủ</span>
      </button>
      <button
        className={`nav-item ${activeTab === 'coopsTab' ? 'active' : ''}`}
        onClick={() => onSwitchTab('coopsTab')}
      >
        <div className="nav-icon">🐔</div>
        <span>Quản lý gà</span>
      </button>
      <button
        className={`nav-item ${activeTab === 'financialTab' ? 'active' : ''}`}
        onClick={() => onSwitchTab('financialTab')}
      >
        <div className="nav-icon">💵</div>
        <span>Tài chính</span>
      </button>
      <button
        className={`nav-item ${activeTab === 'financeManagementTab' ? 'active' : ''}`}
        onClick={() => onSwitchTab('financeManagementTab')}
      >
        <div className="nav-icon">📊</div>
        <span>Quản lí TC</span>
      </button>
      <button
        className={`nav-item ${activeTab === 'devicesTab' ? 'active' : ''}`}
        onClick={() => onSwitchTab('devicesTab')}
      >
        <div className="nav-icon">⚙️</div>
        <span>Thiết bị</span>
      </button>
    </nav>
  );
}
