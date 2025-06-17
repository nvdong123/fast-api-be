"""
app/utils/zalo.py
Utility functions for interacting with Zalo API
"""
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import json
import logging
import httpx
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.zalo import TokenCreate
from app.crud.zalo import zalo_token
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def get_valid_token() -> str:
        """
        Lấy valid access token, tự động refresh nếu cần
        """
        db = SessionLocal()
        try:
            current_token = zalo_token.get_latest_token(db)
            
            if not current_token:
                raise HTTPException(
                    status_code=401,
                    detail="Không có token, cần xác thực"
                )
                
            if current_token.expires_at <= datetime.now():
                if not current_token.refresh_token:
                    raise HTTPException(
                        status_code=401,
                        detail="Token hết hạn, cần xác thực lại"
                    )
                    
                new_token = await self.refresh_access_token(
                    current_token.refresh_token
                )
                current_token = zalo_token.create_token(db, new_token)
                
            return current_token.access_token
            
        finally:
            db.close()

def verify_zalo_webhook(body: str, mac: Optional[str], app_secret: str) -> bool:
    """
    Xác thực webhook request từ Zalo.
    
    Args:
        body (str): Raw body của request
        mac (str): MAC signature từ header
        app_secret (str): App secret từ Zalo Developer Portal
        
    Returns:
        bool: True nếu signature hợp lệ, False nếu không
    """
    try:
        if not mac:
            logger.warning("Missing MAC signature in webhook request")
            return False

        # Tính toán HMAC-SHA256
        expected_mac = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        # So sánh MAC an toàn
        is_valid = hmac.compare_digest(expected_mac.lower(), mac.lower())
        
        if not is_valid:
            logger.warning("Invalid MAC signature in webhook request")
            
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False
        
def verify_webhook_data(data: Dict) -> bool:
    """
    Kiểm tra tính hợp lệ của webhook data
    
    Args:
        data (Dict): Data từ webhook request
        
    Returns:
        bool: True nếu data hợp lệ, False nếu không
    """
    required_fields = ['app_id', 'event_name', 'timestamp']
    
    try:
        # Kiểm tra các trường bắt buộc
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in webhook data: {field}")
                return False
                
        # Kiểm tra app_id
        if data['app_id'] != settings.ZALO_APP_ID:
            logger.warning("Invalid app_id in webhook data")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating webhook data: {str(e)}")
        return False

async def send_zalo_message(
    message_data: Dict,
    access_token: Optional[str] = None,
    retry_count: int = 3
) -> Dict:
    """
    Gửi tin nhắn qua Zalo OA API
    
    Args:
        message_data (Dict): Data tin nhắn cần gửi
        access_token (str, optional): Access token. Nếu không có sẽ tự động lấy token mới
        retry_count (int): Số lần thử lại nếu gặp lỗi
        
    Returns:
        Dict: Response từ Zalo API
        
    Raises:
        HTTPException: Nếu không thể gửi tin nhắn sau số lần thử tối đa
    """
    try:
        # Nếu không có access token, lấy token mới
        if not access_token:
            access_token = await get_valid_token()
            
        # Chuẩn bị headers
        headers = {
            'access_token': access_token,
            'Content-Type': 'application/json'
        }
        
        # Retry loop
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://openapi.zalo.me/v2.0/oa/message',
                        headers=headers,
                        json=message_data,
                        timeout=30.0
                    )
                    
                    # Kiểm tra response
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        # Kiểm tra error trong response data
                        if response_data.get('error') == 0:  # 0 means success in Zalo API
                            logger.info(f"Message sent successfully: {response_data}")
                            return response_data
                            
                        # Xử lý các error codes cụ thể
                        error_code = response_data.get('error')
                        if error_code in [213, 214]:  # Token expired/invalid
                            logger.warning("Token expired/invalid, getting new token...")
                            access_token = await get_valid_token()
                            headers['access_token'] = access_token
                            continue
                            
                    # Log error response
                    logger.error(f"Error response from Zalo API: {response.text}")
                    
                    # Nếu không phải lần thử cuối, đợi trước khi thử lại
                    if attempt < retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    
        # Nếu đã hết số lần thử
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi tin nhắn sau nhiều lần thử"
        )
        
    except Exception as e:
        logger.error(f"Error sending Zalo message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gửi tin nhắn: {str(e)}"
        )

async def send_text_message(
    user_id: str,
    text: str,
    access_token: Optional[str] = None
) -> Dict:
    """
    Gửi tin nhắn text đơn giản
    
    Args:
        user_id (str): ID của người nhận
        text (str): Nội dung tin nhắn
        access_token (str, optional): Access token
        
    Returns:
        Dict: Response từ Zalo API
    """
    message_data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": text
        }
    }
    
    return await send_zalo_message(message_data, access_token)

async def send_image_message(
    user_id: str,
    image_url: str,
    access_token: Optional[str] = None
) -> Dict:
    """
    Gửi tin nhắn hình ảnh
    
    Args:
        user_id (str): ID của người nhận
        image_url (str): URL của hình ảnh
        access_token (str, optional): Access token
        
    Returns:
        Dict: Response từ Zalo API
    """
    message_data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "attachment": {
                "type": "image",
                "payload": {
                    "url": image_url
                }
            }
        }
    }
    
    return await send_zalo_message(message_data, access_token)

async def send_list_template(
    user_id: str,
    elements: List[Dict],
    access_token: Optional[str] = None
) -> Dict:
    """
    Gửi tin nhắn dạng list template
    
    Args:
        user_id (str): ID của người nhận
        elements (List[Dict]): Danh sách các elements trong template
        access_token (str, optional): Access token
        
    Returns:
        Dict: Response từ Zalo API
    """
    message_data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    "elements": elements
                }
            }
        }
    }
    
    return await send_zalo_message(message_data, access_token)

class ZaloAPI:
    """Class để xử lý các tương tác với Zalo API"""
    
    def __init__(self):
        self.app_id = settings.ZALO_APP_ID
        self.app_secret = settings.ZALO_APP_SECRET
        self.callback_url = settings.ZALO_CALLBACK_URL
        self.base_url = "https://openapi.zalo.me/v2.0/oa"
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        access_token: Optional[str] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict:
        """
        Thực hiện request đến Zalo API
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if access_token:
            headers['access_token'] = access_token
            
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30.0
            )
            
        if response.status_code != 200:
            logger.error(f"Zalo API error: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Zalo API error: {response.text}"
            )
            
        return response.json()

    async def get_new_token_from_code(self, code: str) -> TokenCreate:
        """
        Lấy access token mới từ authorization code
        """
        try:
            params = {
                'app_id': self.app_id,
                'app_secret': self.app_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://oauth.zaloapp.com/v4/access_token',
                    params=params
                )
                
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail="Không thể lấy access token"
                )
                
            data = response.json()
            return TokenCreate(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token'),
                expires_at=datetime.now() + timedelta(seconds=data['expires_in'])
            )
            
        except Exception as e:
            logger.error(f"Error getting new token: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Lỗi khi lấy access token"
            )

    async def refresh_access_token(self, refresh_token: str) -> TokenCreate:
        """
        Làm mới access token sử dụng refresh token
        """
        try:
            params = {
                'app_id': self.app_id,
                'app_secret': self.app_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://oauth.zaloapp.com/v4/access_token',
                    params=params
                )
                
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Không thể làm mới access token"
                )
                
            data = response.json()
            return TokenCreate(
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token'),
                expires_at=datetime.now() + timedelta(seconds=data['expires_in'])
            )
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Lỗi khi làm mới access token"
            )

    async def get_valid_token(self) -> str:
        """
        Lấy valid access token, tự động refresh nếu cần
        """
        db = SessionLocal()
        try:
            current_token = zalo_token.get_latest_token(db)
            
            if not current_token:
                raise HTTPException(
                    status_code=401,
                    detail="Không có token, cần xác thực"
                )
                
            if current_token.expires_at <= datetime.now():
                if not current_token.refresh_token:
                    raise HTTPException(
                        status_code=401,
                        detail="Token hết hạn, cần xác thực lại"
                    )
                    
                new_token = await self.refresh_access_token(
                    current_token.refresh_token
                )
                current_token = zalo_token.create_token(db, new_token)
                
            return current_token.access_token
            
        finally:
            db.close()

    def verify_webhook_signature(self, body: str, mac: Optional[str]) -> bool:
        """
        Xác thực signature của webhook request
        """
        if not mac:
            return False

        expected_mac = hmac.new(
            self.app_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_mac, mac)

    async def send_message(
        self,
        user_id: str,
        message_text: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Gửi tin nhắn text đến user
        """
        if not token:
            token = await self.get_valid_token()
            
        message_data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": message_text
            }
        }
        
        return await self._make_request(
            method="POST",
            endpoint="message",
            access_token=token,
            json_data=message_data
        )

    async def send_image_message(
        self,
        user_id: str,
        image_url: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Gửi tin nhắn hình ảnh đến user
        """
        if not token:
            token = await self.get_valid_token()
            
        message_data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": image_url
                    }
                }
            }
        }
        
        return await self._make_request(
            method="POST",
            endpoint="message",
            access_token=token,
            json_data=message_data
        )

    async def get_user_profile(
        self,
        user_id: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Lấy thông tin profile của user
        """
        if not token:
            token = await self.get_valid_token()
            
        return await self._make_request(
            method="GET",
            endpoint="getprofile",
            access_token=token,
            params={"data": json.dumps({"user_id": user_id})}
        )

    async def send_welcome_message(self, user_id: str) -> Dict:
        """
        Gửi tin nhắn chào mừng khi user follow OA
        """
        welcome_text = (
            "Cảm ơn bạn đã quan tâm đến Official Account của chúng tôi! 🎉\n\n"
            "Chúng tôi rất vui mừng được chào đón bạn!\n\n"
            "Bạn sẽ nhận được những thông tin mới nhất về:\n"
            "• Sản phẩm và dịch vụ mới\n"
            "• Khuyến mãi đặc biệt\n"
            "• Tin tức và cập nhật\n\n"
            "Hãy tiếp tục theo dõi để không bỏ lỡ những thông tin hữu ích nhé! 💫"
        )
        
        return await self.send_message(user_id, welcome_text)

    async def tag_user(
        self,
        user_id: str,
        tag_name: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Gắn tag cho user
        """
        if not token:
            token = await self.get_valid_token()
            
        data = {
            "user_id": user_id,
            "tag_name": tag_name
        }
        
        return await self._make_request(
            method="POST",
            endpoint="tag/tagfollow",
            access_token=token,
            json_data=data
        )

    async def remove_user_tag(
        self,
        user_id: str,
        tag_name: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Gỡ tag của user
        """
        if not token:
            token = await self.get_valid_token()
            
        data = {
            "user_id": user_id,
            "tag_name": tag_name
        }
        
        return await self._make_request(
            method="POST",
            endpoint="tag/rmfollow",
            access_token=token,
            json_data=data
        )

    async def send_notification_template(
        self,
        user_id: str,
        template_id: str,
        template_data: Dict[str, Any]
    ) -> Dict:
        """
        Gửi notification template qua Zalo Mini App
        """
        try:
            # Lấy access token
            access_token = await self.get_valid_token()
            
            headers = {
                'X-Api-Key': f'Bearer {access_token}',
                'X-User-Id': user_id,
                'X-MiniApp-Id': self.mini_app_id,
                'Content-Type': 'application/json'
            }
            
            data = {
                "templateId": template_id,
                "templateData": template_data
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://openapi.mini.zalo.me/notification/template',
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
            if response.status_code != 200:
                logger.error(f"Error sending notification template: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Không thể gửi notification template"
                )
                
            response_data = response.json()
            logger.info(f"Sent notification template successfully: {response_data}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error sending notification template: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi khi gửi notification template: {str(e)}"
            )

    async def send_booking_notification(
        self,
        user_id: str,
        booking_data: Dict,
        template_id: Optional[str] = None
    ) -> Dict:
        """
        Gửi notification về đặt phòng
        """
        try:
            # Template mặc định nếu không có template_id
            template_id = template_id or settings.ZALO_BOOKING_TEMPLATE_ID
            
            # Tạo template data
            template_data = {
                "buttonText": "Xem chi tiết đặt phòng",
                "buttonUrl": f"{settings.MINI_APP_URL}/booking/{booking_data['booking_id']}",
                "title": f"{settings.HOTEL_NAME} - Xác nhận đặt phòng",
                "contentTitle": "Xác nhận đặt phòng",
                "contentDescription": f"""
                    Chúng tôi đã nhận yêu cầu đặt phòng từ bạn.
                    
                    🏨 Phòng: {booking_data['room_name']}
                    📅 Check-in: {booking_data['check_in']}
                    📅 Check-out: {booking_data['check_out']}
                    👥 Số người: {booking_data['guests']}
                    💰 Tổng tiền: {booking_data['total_price']:,}đ
                    
                    Vui lòng kiểm tra thông tin chi tiết đơn đặt phòng.
                """.strip()
            }
            
            # Gửi notification
            return await self.send_notification_template(
                user_id=user_id,
                template_id=template_id,
                template_data=template_data
            )
            
        except Exception as e:
            logger.error(f"Error sending booking notification: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi khi gửi thông báo đặt phòng: {str(e)}"
            )


# Khởi tạo instance của ZaloAPI để sử dụng
zalo_api = ZaloAPI()
