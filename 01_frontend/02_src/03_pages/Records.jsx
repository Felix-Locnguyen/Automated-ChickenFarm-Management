import FlockManagement from '../02_components/02.3_Records/FlockManagement.jsx';
import HealthRecords from '../02_components/02.3_Records/HealthRecords.jsx';
import ProductionLog from '../02_components/02.3_Records/ProductionLog.jsx';

export default function Records() {
  return (
    <div className="tab-content active">
      <h2 className="section-title" style={{ fontSize: '18px', marginBottom: '12px' }}>📊 Hồ sơ & Sản xuất</h2>
      <FlockManagement />
      <HealthRecords />
      <ProductionLog />
    </div>
  );
}
