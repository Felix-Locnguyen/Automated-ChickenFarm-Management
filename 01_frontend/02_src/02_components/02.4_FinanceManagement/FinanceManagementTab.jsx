import { useState, useMemo } from 'react';
import FilterBar from './FilterBar.jsx';
import FinanceChart from './FinanceChart.jsx';
import FinanceSummary from './FinanceSummary.jsx';

function groupByDate(records, days) {
  const now = new Date();
  const grouped = {};

  if (days === 7) {
    const dayOfWeek = now.getDay();
    const mondayOffset = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    const monday = new Date(now);
    monday.setDate(now.getDate() - mondayOffset);
    monday.setHours(0, 0, 0, 0);

    const dayNames = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
    dayNames.forEach(name => grouped[name] = { revenue: 0, expense: 0 });

    records.forEach(r => {
      const d = new Date(r.date);
      d.setHours(0, 0, 0, 0);
      const diff = Math.floor((d - monday) / 86400000);
      if (diff >= 0 && diff < 7) {
        const dayIdx = (d.getDay() + 6) % 7;
        const key = dayNames[dayIdx];
        if (r.type === 'income') grouped[key].revenue += r.total || 0;
        else grouped[key].expense += r.total || 0;
      }
    });
  } else if (days === 30) {
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    for (let i = 1; i <= daysInMonth; i++) {
      grouped[i] = { revenue: 0, expense: 0 };
    }
    records.forEach(r => {
      const d = new Date(r.date);
      const key = d.getDate();
      if (grouped[key]) {
        if (r.type === 'income') grouped[key].revenue += r.total || 0;
        else grouped[key].expense += r.total || 0;
      }
    });
  } else {
    for (let i = 1; i <= 12; i++) {
      grouped[`Th${i}`] = { revenue: 0, expense: 0 };
    }
    records.forEach(r => {
      const d = new Date(r.date);
      const key = `Th${d.getMonth() + 1}`;
      if (r.type === 'income') grouped[key].revenue += r.total || 0;
      else grouped[key].expense += r.total || 0;
    });
  }

  return grouped;
}

export default function FinanceManagementTab({ records }) {
  const [filterDays, setFilterDays] = useState(7);

  const grouped = useMemo(() => groupByDate(records, filterDays), [records, filterDays]);
  const labels = Object.keys(grouped);

  const totalRevenue = labels.reduce((s, k) => s + grouped[k].revenue, 0);
  const totalExpense = labels.reduce((s, k) => s + grouped[k].expense, 0);
  const totalProfit = totalRevenue - totalExpense;

  const yMax = Math.max(1, ...labels.map(k => Math.max(grouped[k].revenue, grouped[k].expense)));
  const yMin = Math.min(0, ...labels.map(k => grouped[k].revenue - grouped[k].expense));

  return (
    <div className="tab-content active">
      <h3 className="section-title">📊 Quản lý tài chính</h3>

      <FilterBar activeFilter={filterDays} onFilterChange={setFilterDays} />

      <div className="card card-default" style={{ padding: '16px', marginBottom: '12px' }}>
        <FinanceChart labels={labels} grouped={grouped} yMax={yMax} yMin={yMin} />
      </div>

      <FinanceSummary totalRevenue={totalRevenue} totalExpense={totalExpense} totalProfit={totalProfit} />
    </div>
  );
}
