# Somalia Geography API - CRUD operations
# User authentication functions for login/registration

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


def get_user_by_email(session: Session, email: str) -> User | None:
    """Get user by email."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user(session: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def authenticate(session: Session, email: str, password: str) -> User | None:
    """Authenticate a user."""
    user = get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(session: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name,
        is_superuser=user_create.is_superuser,
        is_active=user_create.is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, db_user: User, user_in: UserUpdate) -> User:
    """Update a user."""
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def create_item(session: Session, item_in: ItemCreate, owner_id: int) -> Item:
    """Create a new item."""
    item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
