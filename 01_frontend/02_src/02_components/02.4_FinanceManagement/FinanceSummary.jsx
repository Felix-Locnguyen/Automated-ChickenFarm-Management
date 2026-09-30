export default function FinanceSummary({ totalRevenue, totalExpense, totalProfit }) {
  return (
    <div className="fm-summary-grid">
      <div className="fm-summary-box fm-revenue">
        <span className="fm-summary-icon">💵</span>
        <span className="fm-summary-label">Tổng thu</span>
        <span className="fm-summary-value">{totalRevenue.toLocaleString('vi-VN')} ₫</span>
      </div>
      <div className="fm-summary-box fm-expense">
        <span className="fm-summary-icon">💸</span>
        <span className="fm-summary-label">Tổng chi</span>
        <span className="fm-summary-value">{totalExpense.toLocaleString('vi-VN')} ₫</span>
      </div>
      <div className="fm-summary-box fm-profit">
        <span className="fm-summary-icon">📈</span>
        <span className="fm-summary-label">Lợi nhuận</span>
        <span className="fm-summary-value">{totalProfit.toLocaleString('vi-VN')} ₫</span>
      </div>
    </div>
  );
}
