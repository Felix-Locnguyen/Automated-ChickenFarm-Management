export default function FilterBar({ activeFilter, onFilterChange }) {
  const filters = [
    { days: 7, label: '7 ngày' },
    { days: 30, label: '30 ngày' },
    { days: 365, label: '12 tháng' }
  ];

  return (
    <div className="fm-filter-bar">
      {filters.map(f => (
        <button
          key={f.days}
          className={`fm-filter ${activeFilter === f.days ? 'active' : ''}`}
          onClick={() => onFilterChange(f.days)}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}
