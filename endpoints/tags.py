from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Tag, TagCreate, TagUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/tags/")
async def get_tags(db: Session = Depends(get_db)):
    items = db.query(Tag).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    return result

@router.get("/tags/{tag_id}", response_model=TagCreate)
async def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag\
    
@router.post("/tags/", status_code=status.HTTP_201_CREATED, response_model=TagCreate)
async def add_tag(tag: TagCreate, db: Session = Depends(get_db)):
    db_tag = Tag(**tag.dict())
    db.add(db_tag)
    try:
        db.commit()
        db.refresh(db_tag)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_tag

@router.put("/tags/{tag_id}", response_model=TagCreate)
async def update_tag(tag_id: int, tag_update: TagUpdate, db: Session =  Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    for key, value in tag_update.dict(exclude_unset=True).items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()
    return
    