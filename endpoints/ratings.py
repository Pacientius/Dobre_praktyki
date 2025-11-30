from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.models import Rating, RatingCreate, RatingUpdate
from database.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ratings/")
async def get_ratings(db: Session = Depends(get_db)):
    items = db.query(Rating).all()
    result = [x.__dict__ for x in items]
    for r in result:
        r.pop("_sa_instance_state", None)
    return result

@router.get("/ratings/{rating_id}", response_model=RatingCreate)
async def get_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating

@router.post("/ratings/", status_code=status.HTTP_201_CREATED, response_model=RatingCreate)
async def add_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    db_rating = Rating(**rating.dict())
    db.add(db_rating)
    try:
        db.commit()
        db.refresh(db_rating)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_rating

@router.put("/ratings/{rating_id}", response_model=RatingCreate)
async def update_rating(rating_id: int, rating_update: RatingUpdate, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    for key, value in rating_update.dict(exclude_unset=True).items():
        setattr(rating, key, value)

    db.commit()
    db.refresh(rating)
    return rating

@router.delete("/ratings/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(rating_id: int, db: Session = Depends(get_db)): 
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    db.delete(rating)
    db.commit() 
    return 

