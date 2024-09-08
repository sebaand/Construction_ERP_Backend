from app.models.user import User
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db_session):
        self.db_session = db_session

    def create_user(self, user: UserCreate):
        db_user = User(**user.dict())
        self.db_session.add(db_user)
        self.db_session.commit()
        return db_user

    def get_user(self, user_id: int):
        return self.db_session.query(User).filter(User.id == user_id).first()