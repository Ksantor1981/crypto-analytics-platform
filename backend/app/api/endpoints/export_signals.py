"""
Export signals as CSV.
"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.signal import Signal
from app.models.user import User

router = APIRouter()


@router.get("/export/signals.csv")
async def export_signals_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all signals as CSV file."""
    signals = db.query(Signal).options(joinedload(Signal.channel)).order_by(Signal.created_at.desc()).limit(1000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Asset", "Direction", "Entry Price", "Take Profit", "Stop Loss",
        "Status", "PnL %", "Channel", "Confidence", "Created At",
    ])

    for s in signals:
        writer.writerow([
            s.id,
            s.asset,
            s.direction,
            float(s.entry_price) if s.entry_price else "",
            float(s.tp1_price) if s.tp1_price else "",
            float(s.stop_loss) if s.stop_loss else "",
            s.status,
            float(s.profit_loss_percentage) if s.profit_loss_percentage else "",
            s.channel.name if s.channel else "",
            float(s.confidence_score) if s.confidence_score else "",
            s.created_at.isoformat() if s.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=signals_export.csv"},
    )
