from auth import get_password_hash
from database.database import get_db
from database.model import User


def create_admin_user(db=None):
    created_session = False
    if db is None:
        db = next(get_db())
        created_session = True

    try:
        user = db.query(User).filter(User.name == "admin").first()
        if not user:
            hashed_pw = get_password_hash("admin123")
            admin_user = User(name="admin", password=hashed_pw, roles=["ADMIN", "USER"])
            db.add(admin_user)
            db.commit()
            print("Admin user created.")
    finally:
        if created_session:
            db.close()