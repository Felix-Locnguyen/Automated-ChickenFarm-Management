"""Phiếu thu/chi tài chính.

Có 2 nhóm trường:
- Do USER nhập: quantity_before, cost_per_chick, dead_chickens, sold_chickens,
  unit_price, feed_cost, other_cost, note
- Do BACKEND tự tính (xem hàm calculate_fields trong api/financial.py):
  depreciation_cost, revenue, total_cost, profit
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...database import Base


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    flock_id = Column(Integer, ForeignKey("flocks.id"))
    date = Column(DateTime(timezone=True))

    # --- do user nhập ---
    quantity_before = Column(Integer, default=0)  # số gà đầu kỳ
    cost_per_chick = Column(Float, default=0)     # giá mỗi con mua vào
    dead_chickens = Column(Integer, default=0)    # số gà chết
    sold_chickens = Column(Integer, default=0)    # số gà bán
    unit_price = Column(Float, default=0)         # đơn giá bán
    feed_cost = Column(Float, default=0)          # tiền thức ăn
    other_cost = Column(Float, default=0)         # chi phí khác
    note = Column(String(500))

    # --- backend tự tính ---
    depreciation_cost = Column(Float, default=0)  # hao hụt = dead_chickens * cost_per_chick
    revenue = Column(Float, default=0)            # doanh thu = sold_chickens * unit_price
    total_cost = Column(Float, default=0)         # tổng chi phí
    profit = Column(Float, default=0)             # lợi nhuận = revenue - total_cost

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    flock = relationship("Flock", back_populates="financial_records")
