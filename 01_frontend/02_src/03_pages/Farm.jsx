import CoopsSearchList from '../02_components/02.2_Farm/CoopsSearchList.jsx';
import CageViewer from '../02_components/02.2_Farm/CageViewer.jsx';

export default function Farm({ coops, selectedCoop, searchQuery, onSearchChange, onSelectCoop, onBack, onToggleDevice, onAddFeed, onRemoveFeed, onUpdateThresholds, onUpdateCoop }) {
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
        />
      </div>
    );
  }

  return (
    <div className="tab-content active">
      <h2 className="section-title" style={{ fontSize: '18px', marginBottom: '12px' }}>Quản lý gà & Chuồng</h2>
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
