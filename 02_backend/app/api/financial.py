from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..database import get_db
from ..models.financial.record import FinancialRecord
from .schemas import FinancialRecordCreate, FinancialRecordResponse

router = APIRouter()


def calculate_fields(data: FinancialRecordCreate) -> dict:
    """Tự động tính toán các trường: khấu hao, doanh thu, tổng chi phí, lợi nhuận"""
    depreciation = data.dead_chickens * data.unit_price
    revenue = data.sold_chickens * data.unit_price
    chick_cost = data.quantity_before * data.cost_per_chick
    total_cost = chick_cost + data.feed_cost + data.other_cost + depreciation
    profit = revenue - total_cost
    return {
        "depreciation_cost": depreciation,
        "revenue": revenue,
        "total_cost": total_cost,
        "profit": profit,
    }


@router.get("/financial", response_model=list[FinancialRecordResponse])
def get_records(
    flock_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    """Lấy danh sách records, có thể lọc theo flock_id và khoảng ngày"""
    query = db.query(FinancialRecord)
    if flock_id:
        query = query.filter(FinancialRecord.flock_id == flock_id)
    if from_date:
        query = query.filter(FinancialRecord.date >= from_date)
    if to_date:
        query = query.filter(FinancialRecord.date <= to_date)
    return query.order_by(FinancialRecord.date.desc()).all()


@router.post("/financial", response_model=FinancialRecordResponse)
def create_record(record: FinancialRecordCreate, db: Session = Depends(get_db)):
    """Tạo record mới, tự động tính toán các trường"""
    calc = calculate_fields(record)
    db_record = FinancialRecord(**record.dict(), **calc)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/financial/summary")
def get_summary(
    flock_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Tổng quan doanh thu, chi phí, lợi nhuận"""
    query = db.query(FinancialRecord)
    if flock_id:
        query = query.filter(FinancialRecord.flock_id == flock_id)
    records = query.all()
    return {
        "total_revenue": sum(r.revenue for r in records),
        "total_cost": sum(r.total_cost for r in records),
        "total_profit": sum(r.profit for r in records),
        "total_depreciation": sum(r.depreciation_cost for r in records),
        "record_count": len(records),
    }


@router.get("/financial/{record_id}", response_model=FinancialRecordResponse)
def get_record(record_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết 1 record"""
    record = (
        db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record không tồn tại")
    return record


@router.put("/financial/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    record_id: int,
    record: FinancialRecordCreate,
    db: Session = Depends(get_db),
):
    """Cập nhật record và tính lại các trường"""
    db_record = (
        db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Record không tồn tại")
    calc = calculate_fields(record)
    for key, value in record.dict().items():
        setattr(db_record, key, value)
    for key, value in calc.items():
        setattr(db_record, key, value)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.delete("/financial/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    """Xóa record"""
    db_record = (
        db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Record không tồn tại")
    db.delete(db_record)
    db.commit()
    return {"message": "Đã xóa"}
