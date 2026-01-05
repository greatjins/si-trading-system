"""
Telegram 알림 유틸리티
"""
import asyncio
from typing import Optional
import aiohttp
from utils.logger import setup_logger
from utils.config import config

logger = setup_logger(__name__)


class TelegramNotifier:
    """
    Telegram 봇을 통한 알림 전송
    
    환경 변수 또는 config에서 다음 설정을 읽습니다:
    - telegram.bot_token: Telegram 봇 토큰
    - telegram.chat_id: 메시지를 보낼 채팅 ID
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """
        Args:
            bot_token: Telegram 봇 토큰 (None이면 config에서 로드)
            chat_id: 채팅 ID (None이면 config에서 로드)
        """
        self.bot_token = bot_token or config.get("telegram.bot_token", "")
        self.chat_id = chat_id or config.get("telegram.chat_id", "")
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot_token or chat_id not configured. Notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("TelegramNotifier initialized")
    
    async def send_message(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Telegram 메시지 전송
        
        Args:
            message: 전송할 메시지
            parse_mode: 파싱 모드 (HTML, Markdown 등)
        
        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping message")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Telegram message: {response.status} - {error_text}")
                        return False
        
        except asyncio.TimeoutError:
            logger.error("Telegram API timeout")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        context: Optional[str] = None
    ) -> bool:
        """
        에러 알림 전송
        
        Args:
            error_message: 에러 메시지
            error_type: 에러 타입
            context: 추가 컨텍스트 정보
        
        Returns:
            전송 성공 여부
        """
        message = f"<b>⚠️ 에러 발생</b>\n\n"
        
        if error_type:
            message += f"<b>타입:</b> {error_type}\n"
        
        message += f"<b>메시지:</b> {error_message}\n"
        
        if context:
            message += f"\n<b>컨텍스트:</b> {context}"
        
        return await self.send_message(message)
    
    async def send_info(
        self,
        title: str,
        message: str
    ) -> bool:
        """
        정보 알림 전송
        
        Args:
            title: 제목
            message: 메시지
        
        Returns:
            전송 성공 여부
        """
        formatted_message = f"<b>{title}</b>\n\n{message}"
        return await self.send_message(formatted_message)
    
    async def send_success(
        self,
        title: str,
        message: str
    ) -> bool:
        """
        성공 알림 전송
        
        Args:
            title: 제목
            message: 메시지
        
        Returns:
            전송 성공 여부
        """
        formatted_message = f"<b>✅ {title}</b>\n\n{message}"
        return await self.send_message(formatted_message)


# 전역 인스턴스
_telegram_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> TelegramNotifier:
    """
    전역 TelegramNotifier 인스턴스 가져오기 (싱글톤)
    
    Returns:
        TelegramNotifier 인스턴스
    """
    global _telegram_notifier
    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier

