# app/crud/zalo.py

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from app.models.zalo import ZaloToken
from app.models.zalo import ZaloUser
from app.models.zalo import ZaloMessage
from app.models.zalo import ZaloUserTag
from app.schemas.zalo import TokenCreate, TokenUpdate
import uuid

class CRUDZaloToken:
    def get_latest_token(self, db: Session) -> Optional[ZaloToken]:
        return db.query(ZaloToken).order_by(desc(ZaloToken.created_at)).first()

    def create_token(self, db: Session, token: TokenCreate) -> ZaloToken:
        db_token = ZaloToken(
            id=str(uuid.uuid4()),
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_at=token.expires_at
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def update_token(self, db: Session, token_id: str, token: TokenUpdate) -> Optional[ZaloToken]:
        db_token = db.query(ZaloToken).filter(ZaloToken.id == token_id).first()
        if db_token:
            for field, value in token.dict(exclude_unset=True).items():
                setattr(db_token, field, value)
            db.commit()
            db.refresh(db_token)
        return db_token

class CRUDZaloUser:
    def get_by_zalo_id(self, db: Session, zalo_id: str) -> Optional[ZaloUser]:
        return db.query(ZaloUser).filter(ZaloUser.zalo_id == zalo_id).first()

    def create(self, db: Session, zalo_id: str, display_name: Optional[str] = None, 
               avatar_url: Optional[str] = None, shared_info: Optional[Dict] = None) -> ZaloUser:
        db_user = ZaloUser(
            id=str(uuid.uuid4()),
            zalo_id=zalo_id,
            display_name=display_name,
            avatar_url=avatar_url,
            shared_info=shared_info,
            is_following=True,
            followed_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(self, db: Session, zalo_id: str, **kwargs) -> Optional[ZaloUser]:
        db_user = self.get_by_zalo_id(db, zalo_id)
        if db_user:
            for key, value in kwargs.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
        return db_user

    def set_follow_status(self, db: Session, zalo_id: str, is_following: bool) -> Optional[ZaloUser]:
        db_user = self.get_by_zalo_id(db, zalo_id)
        if db_user:
            db_user.is_following = is_following
            if is_following:
                db_user.followed_at = datetime.utcnow()
                db_user.unfollowed_at = None
            else:
                db_user.unfollowed_at = datetime.utcnow()
            db.commit()
            db.refresh(db_user)
        return db_user

    def get_all_followers(self, db: Session, skip: int = 0, limit: int = 100) -> List[ZaloUser]:
        return db.query(ZaloUser).filter(ZaloUser.is_following == True)\
                 .offset(skip).limit(limit).all()

class CRUDZaloMessage:
    def create(self, db: Session, user_id: str, message_type: str, 
               content: Optional[str] = None, attachment_type: Optional[str] = None,
               attachment_url: Optional[str] = None, direction: str = "outgoing",
               status: str = "sent", zalo_message_id: Optional[str] = None) -> ZaloMessage:
        db_message = ZaloMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            zalo_message_id=zalo_message_id,
            message_type=message_type,
            content=content,
            attachment_type=attachment_type,
            attachment_url=attachment_url,
            direction=direction,
            status=status
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    def get_user_messages(self, db: Session, user_id: str, 
                         skip: int = 0, limit: int = 100) -> List[ZaloMessage]:
        return db.query(ZaloMessage).filter(ZaloMessage.user_id == user_id)\
                 .order_by(desc(ZaloMessage.created_at))\
                 .offset(skip).limit(limit).all()

    def update_status(self, db: Session, message_id: str, status: str) -> Optional[ZaloMessage]:
        db_message = db.query(ZaloMessage).filter(ZaloMessage.id == message_id).first()
        if db_message:
            db_message.status = status
            db.commit()
            db.refresh(db_message)
        return db_message

class CRUDZaloUserTag:
    def create(self, db: Session, user_id: str, tag_name: str) -> ZaloUserTag:
        db_tag = ZaloUserTag(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tag_name=tag_name
        )
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag

    def remove(self, db: Session, user_id: str, tag_name: str) -> bool:
        deleted = db.query(ZaloUserTag)\
                   .filter(and_(ZaloUserTag.user_id == user_id, 
                               ZaloUserTag.tag_name == tag_name))\
                   .delete()
        db.commit()
        return bool(deleted)

    def get_user_tags(self, db: Session, user_id: str) -> List[ZaloUserTag]:
        return db.query(ZaloUserTag).filter(ZaloUserTag.user_id == user_id).all()

    def get_users_by_tag(self, db: Session, tag_name: str) -> List[ZaloUser]:
        return db.query(ZaloUser)\
                 .join(ZaloUserTag)\
                 .filter(ZaloUserTag.tag_name == tag_name)\
                 .all()

# Khởi tạo các instance để sử dụng
zalo_token = CRUDZaloToken()
zalo_user = CRUDZaloUser()
zalo_message = CRUDZaloMessage()
zalo_user_tag = CRUDZaloUserTag()