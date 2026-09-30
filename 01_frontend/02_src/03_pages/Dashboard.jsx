import EnvironmentMonitor from '../02_components/02.1_Dashboard/EnvironmentMonitor.jsx';
import DiseaseDetectionBox from '../02_components/02.1_Dashboard/DiseaseDetectionBox.jsx';
import CoopsList from '../02_components/02.2_Farm/CoopsList.jsx';
import AlertPanel from '../02_components/02.1_Dashboard/AlertPanel.jsx';

export default function Dashboard({ farmData, onSelectCoop, showAlertModal, onShowAlert, onCloseAlert }) {
  return (
    <div className="tab-content active">
      <EnvironmentMonitor
        avgTemperature={farmData.avgTemperature}
        avgHumidity={farmData.avgHumidity}
        coops={farmData.coops}
        activeAlertsCount={farmData.activeAlertsCount}
      />
      <DiseaseDetectionBox detections={farmData.diseaseDetections} />
      <h3 className="section-title">🏠 Danh sách chuồng nuôi</h3>
      <CoopsList coops={farmData.coops} onSelectCoop={onSelectCoop} />

      {showAlertModal && (
        <AlertPanel
          alerts={farmData.alerts}
          activeAlertsCount={farmData.activeAlertsCount}
          show={showAlertModal}
          onClose={onCloseAlert}
        />
      )}
    </div>
  );
}
