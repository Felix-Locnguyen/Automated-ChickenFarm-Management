import { useState } from 'react';
import IncomeForm from './IncomeForm.jsx';
import ExpenseForm from './ExpenseForm.jsx';
import RecentRecords from './RecentRecords.jsx';
import HistoryModal from './HistoryModal.jsx';
import RecordDetailModal from './RecordDetailModal.jsx';

export default function FinancialTab({ coops, records, onSaveRecord, onEditRecord, onDeleteRecord }) {
  const [activeFinTab, setActiveFinTab] = useState('income');
  const [showHistory, setShowHistory] = useState(false);
  const [detailRecord, setDetailRecord] = useState(null);

  const handleSave = (record) => {
    onSaveRecord(record);
  };

  const handleEdit = (record) => {
    setDetailRecord(null);
    setActiveFinTab(record.type === 'income' ? 'income' : 'expense');
    onEditRecord(record.id, record);
  };

  const handleDelete = (id, record) => {
    setDetailRecord(null);
    onDeleteRecord(id, record);
  };

  return (
    <div className="tab-content active">
      <h3 className="section-title">💵 Nhập tài chính</h3>

      <div className="fin-tab-bar">
        <button
          className={`fin-tab-btn ${activeFinTab === 'income' ? 'active' : ''}`}
          onClick={() => setActiveFinTab('income')}
        >
          💵 Thu
        </button>
        <button
          className={`fin-tab-btn ${activeFinTab === 'expense' ? 'active' : ''}`}
          onClick={() => setActiveFinTab('expense')}
        >
          💸 Chi
        </button>
      </div>

      {activeFinTab === 'income' ? (
        <IncomeForm coops={coops} onSave={handleSave} />
      ) : (
        <ExpenseForm coops={coops} onSave={handleSave} />
      )}

      <div className="fin-list-header">
        <h3 className="section-title" style={{ margin: 0 }}>📋 Gần đây</h3>
        <button className="btn-history" onClick={() => setShowHistory(true)}>☰</button>
      </div>

      <RecentRecords records={records} onViewDetail={setDetailRecord} />

      {showHistory && (
        <HistoryModal
          records={records}
          onClose={() => setShowHistory(false)}
          onViewDetail={(rec) => { setShowHistory(false); setDetailRecord(rec); }}
        />
      )}

      {detailRecord && (
        <RecordDetailModal
          record={detailRecord}
          onClose={() => setDetailRecord(null)}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onEditSave={onEditRecord}
        />
      )}
    </div>
  );
}
