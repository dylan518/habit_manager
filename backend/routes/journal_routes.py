from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import Journal, JournalSection, DailyRecord
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime, date


router = APIRouter()

class JournalResponse(BaseModel):
    id: int
    date: datetime

class JournalSectionResponse(BaseModel):
    header: str
    content: str

class JournalDetailResponse(BaseModel):
    date: datetime
    sections: List[JournalSectionResponse]

class JournalCreate(BaseModel):
    sections: List[Dict[str, str]]

@router.get("/journals/{journal_id}", response_model=JournalDetailResponse)
def get_journal(journal_id: int, db: Session = Depends(get_db)):
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="Journal not found")
    sections = (
        db.query(JournalSection)
        .filter(JournalSection.journal_id == journal_id)
        .order_by(JournalSection.order)
        .all()
    )
    return {
        "date": journal.exact_time,
        "sections": [{"header": s.header, "content": s.content} for s in sections],
    }

@router.get("/journals", response_model=List[JournalResponse])
def get_all_journals(db: Session = Depends(get_db)):
    journals = db.query(Journal).order_by(Journal.exact_time.desc()).all()
    return [{"id": j.id, "date": j.exact_time} for j in journals]

@router.post("/journals")
def add_journal(journal: JournalCreate, db: Session = Depends(get_db)):
    today = date.today()
    daily_record = db.query(DailyRecord).filter(DailyRecord.date == today).first()
    if not daily_record:
        daily_record = DailyRecord(date=today)
        db.add(daily_record)
        db.commit()
    
    new_journal = Journal(exact_time=datetime.now(), daily_record_id=daily_record.id)
    db.add(new_journal)
    db.flush()  # This will assign an id to new_journal
    
    for i, section in enumerate(journal.sections):
        new_section = JournalSection(
            journal_id=new_journal.id,
            header=section["header"],
            content=section["content"],
            order=i,
        )
        db.add(new_section)
    
    db.commit()
    return {"message": "Journal added successfully", "journal_id": new_journal.id}
