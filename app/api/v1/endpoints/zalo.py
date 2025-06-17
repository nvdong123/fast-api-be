# app/api/v1/endpoints/zalo.py

from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.utils.zalo import verify_zalo_webhook, send_zalo_message
from typing import Optional
import hmac
import hashlib
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def zalo_webhook(
    request: Request,
    mac: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Xử lý webhook events từ Zalo OA
    URL: https://zalo-api.ailab.vn/api/v1/zalo/webhook
    """
    try:
        # Đọc raw body
        body = await request.body()
        body_str = body.decode()

        # print(body_str)

        # Verify webhook signature
        # if not verify_webhook_signature(body_str, mac):
        #     raise HTTPException(status_code=403, detail="Invalid signature")

        print('OK')
        # Parse JSON body
        data = json.loads(body_str)
        event = data.get("event_name")

        # Log event
        logger.info(f"Received Zalo event: {event}")
        logger.debug(f"Event data: {data}")

        # Xử lý các loại event
        if event == "follow":
            await handle_follow_event(data, db)
        elif event == "unfollow":
            await handle_unfollow_event(data, db)
        elif event == "user_send_text":
            await handle_user_message_event(data, db)
        # Thêm các event khác nếu cần

        return {"status": "success"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        print(e)
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def verify_webhook_signature(body: str, mac: Optional[str]) -> bool:
    """
    Xác thực signature của webhook request
    """
    if not mac:
        return False

    expected_mac = hmac.new(
        settings.ZALO_APP_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_mac, mac)

async def handle_follow_event(data: dict, db: Session):
    """
    Xử lý khi user follow OA
    """
    user_id = data.get("follower", {}).get("id")
    if not user_id:
        logger.error("Missing user_id in follow event")
        return

    try:
        # Gửi tin nhắn chào mừng
        welcome_message = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": "Cảm ơn bạn đã quan tâm đến Official Account của chúng tôi! 🎉\n\n" +
                        "Chúng tôi rất vui mừng được chào đón bạn!"
            }
        }
        
        # Gọi API gửi tin nhắn
        await send_zalo_message(welcome_message)
        
        # Cập nhật database nếu cần
        # TODO: Thêm logic cập nhật DB
        
    except Exception as e:
        logger.error(f"Error handling follow event: {str(e)}")

async def handle_unfollow_event(data: dict, db: Session):
    """
    Xử lý khi user unfollow OA
    """
    user_id = data.get("follower", {}).get("id")
    if not user_id:
        logger.error("Missing user_id in unfollow event")
        return

    try:
        # Cập nhật trạng thái trong DB
        # TODO: Thêm logic cập nhật DB
        pass
    except Exception as e:
        logger.error(f"Error handling unfollow event: {str(e)}")

async def handle_user_message_event(data: dict, db: Session):
    """
    Xử lý khi user gửi tin nhắn đến OA
    """
    user_id = data.get("sender", {}).get("id")
    message = data.get("message", {}).get("text")

    print(user_id)

    if not user_id or not message:
        logger.error("Missing user_id or message in user_send_text event")
        return

    try:
        # Xử lý tin nhắn từ user (có thể thêm chatbot hoặc forward đến admin)
        response_message = {
            "recipient": {
                "user_id": 3876824220175160774
            },
            "message": {
                "text": "Cảm ơn bạn đã gửi tin nhắn. Chúng tôi sẽ phản hồi sớm nhất có thể!"
            }
        }
        
        await send_zalo_message(response_message)
        
    except Exception as e:
        logger.error(f"Error handling user message event: {str(e)}")