import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Candidate, Hall, PaperSet, SeatPlan
from app.services.seat_engine import find_violations, place_candidates, plan_to_dict

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.get("")
def list_candidates(db: Session = Depends(get_db)):
    return [{"id": r.id, "hall_id": r.hall_id, "name": r.name, "ticket_no": r.ticket_no, "paper_id": r.paper_id}
            for r in db.scalars(select(Candidate).order_by(Candidate.id)).all()]

class PaperChange(BaseModel):
    paper_id: int

@router.patch("/{candidate_id}")
def change_paper(candidate_id: int, body: PaperChange, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "考生不存在")
    if not db.get(PaperSet, body.paper_id):
        raise HTTPException(404, "试卷套不存在")
    try:
        cand.paper_id = body.paper_id
        plan_id = None
        has_plan = (db.scalar(select(func.count()).select_from(SeatPlan)
                              .where(SeatPlan.hall_id == cand.hall_id)) or 0) > 0
        if has_plan:
            # A live plan exists: set change, latest graph and violations commit together or not at all.
            hall = db.get(Hall, cand.hall_id)
            cands = [{"id": c.id, "name": c.name, "ticket_no": c.ticket_no, "paper_id": c.paper_id}
                     for c in db.scalars(select(Candidate).where(Candidate.hall_id == hall.id)).all()]
            assigns, unplaced = place_candidates(hall.rows, hall.cols, hall.min_manhattan, cands)
            viols = find_violations(hall.rows, hall.cols, hall.min_manhattan, assigns)
            result = plan_to_dict(assigns, unplaced, viols, hall.rows, hall.cols)
            result["hall"] = {"id": hall.id, "name": hall.name, "min_manhattan": hall.min_manhattan}
            plan = SeatPlan(hall_id=hall.id, created_at=datetime.utcnow(),
                            result_json=json.dumps(result, ensure_ascii=False))
            db.add(plan)
            db.flush()
            plan_id = plan.id
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "改卷套与重排未提交，已整体回滚")
    return {"id": cand.id, "hall_id": cand.hall_id, "name": cand.name,
            "ticket_no": cand.ticket_no, "paper_id": cand.paper_id, "plan_id": plan_id}
