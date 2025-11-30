from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Link, LinkCreate, LinkUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/links/")
async def get_links(db: Session = Depends(get_db)):
    items = db.query(Link).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    return result

@router.get("/links/{link_id}", response_model=LinkCreate)
async def get_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@router.post("/links/", status_code=status.HTTP_201_CREATED, response_model=LinkCreate)
async def add_link(link: LinkCreate, db: Session = Depends(get_db)):
    db_link = Link(**link.dict())
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_link

@router.put("/links/{link_id}", response_model=LinkCreate)
async def update_link(link_id: int, link_update: LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    for key, value in link_update.dict(exclude_unset=True).items():
        setattr(link, key, value)

    db.commit()
    db.refresh(link)
    return link

@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    return

"""
@router.get("/links")
def get_links():
    db = SessionLocal()
    items = db.query(Link).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    db.close()
    return result
"""