import { useState, useEffect, useRef } from 'react';

function formatShortNumber(num) {
  if (num >= 1000000000) return (num / 1000000000).toFixed(1) + ' tỷ';
  if (num >= 1000000) return (num / 1000000).toFixed(1) + ' tr';
  if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
  return num.toLocaleString('vi-VN');
}

const CHART_HEIGHT = 180;

export default function FinanceChart({ labels, grouped, yMax, yMin }) {
  const [mounted, setMounted] = useState(false);
  const [barPositions, setBarPositions] = useState([]);
  const chartRef = useRef(null);

  const yRange = yMax - yMin || 1;

  useEffect(() => {
    if (!chartRef.current || labels.length === 0) return;
    const groups = chartRef.current.querySelectorAll('.fm-bar-group');
    const positions = Array.from(groups).map(group => {
      const rect = group.getBoundingClientRect();
      const chartRect = chartRef.current.getBoundingClientRect();
      return {
        centerX: rect.left - chartRect.left + rect.width / 2
      };
    });
    setBarPositions(positions);
    requestAnimationFrame(() => setMounted(true));
  }, [labels, grouped]);

  if (labels.length === 0) {
    return (
      <p style={{ textAlign: 'center', color: '#a0826d', fontSize: '13px', padding: '24px 0' }}>
        Không có dữ liệu
      </p>
    );
  }

  const chartWidth = chartRef.current?.offsetWidth || 300;

  const profitPoints = labels.map((label, idx) => {
    const item = grouped[label];
    const profit = item.revenue - item.expense;
    const x = barPositions[idx]?.centerX || 0;
    const y = CHART_HEIGHT - ((profit - yMin) / yRange) * CHART_HEIGHT;
    return { x, y, profit };
  });

  const pathD = profitPoints.map((p, i) =>
    `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
  ).join(' ');

  return (
    <div className="fm-chart-wrapper">
      <div className="fm-chart-container">
        <div className="fm-y-axis">
          {[yMax, Math.round(yMax / 2), 0, ...(yMin < 0 ? [yMin] : [])].map((v, i) => (
            <span key={i}>{formatShortNumber(v)}</span>
          ))}
        </div>
        <div className="fm-chart" ref={chartRef}>
          {labels.map((label, idx) => {
            const item = grouped[label];
            const hRevenue = yMax > 0 ? (item.revenue / yMax) * CHART_HEIGHT : 0;
            const hExpense = yMax > 0 ? (item.expense / yMax) * CHART_HEIGHT : 0;
            return (
              <div key={idx} className="fm-bar-group">
                <div className="fm-bars">
                  <div className="fm-bar-col">
                    <span className="fm-bar-value">
                      {item.revenue > 0 ? formatShortNumber(item.revenue) : ''}
                    </span>
                    <div
                      className="fm-bar fm-bar-revenue"
                      style={{ height: mounted ? `${hRevenue}px` : '0px' }}
                    ></div>
                  </div>
                  <div className="fm-bar-col">
                    <span className="fm-bar-value">
                      {item.expense > 0 ? formatShortNumber(item.expense) : ''}
                    </span>
                    <div
                      className="fm-bar fm-bar-expense"
                      style={{ height: mounted ? `${hExpense}px` : '0px' }}
                    ></div>
                  </div>
                </div>
                <span className="fm-bar-label">{label}</span>
              </div>
            );
          })}

          {yMin < 0 && (
            <div className="fm-zero-line" style={{
              bottom: `${(-yMin / yRange) * 100}%`
            }}></div>
          )}

          <svg
            className="fm-profit-line"
            width={chartWidth}
            height={CHART_HEIGHT}
            style={{ left: 0, top: 0 }}
          >
            <path
              d={pathD}
              className="fm-profit-path"
              style={{
                strokeDasharray: 1000,
                strokeDashoffset: mounted ? 0 : 1000,
                transition: 'stroke-dashoffset 0.8s ease-out'
              }}
            />
            {profitPoints.map((p, i) => (
              <circle
                key={i}
                cx={p.x}
                cy={p.y}
                r={mounted ? 4 : 0}
                className="fm-profit-dot"
                style={{ transition: 'r 0.3s ease-out 0.6s' }}
              >
                <title>{`Lợi nhuận: ${p.profit.toLocaleString('vi-VN')}đ`}</title>
              </circle>
            ))}
          </svg>
        </div>
      </div>

      <div className="fm-legend">
        <div className="fm-legend-item">
          <span className="fm-legend-color" style={{ backgroundColor: '#16a34a' }}></span> Thu
        </div>
        <div className="fm-legend-item">
          <span className="fm-legend-color" style={{ backgroundColor: '#dc2626' }}></span> Chi
        </div>
        <div className="fm-legend-item">
          <span className="fm-legend-color fm-legend-line"></span> Lợi nhuận
        </div>
      </div>
    </div>
  );
}
