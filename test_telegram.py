"""
텔레그램 알림 테스트 스크립트
"""
import asyncio
from utils.notifier import get_telegram_notifier
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_telegram():
    """텔레그램 알림 테스트"""
    print("=" * 60)
    print("텔레그램 알림 테스트")
    print("=" * 60)
    print()
    
    # TelegramNotifier 가져오기
    notifier = get_telegram_notifier()
    
    if not notifier.enabled:
        print("[X] 텔레그램 알림이 비활성화되어 있습니다.")
        print("   config.yaml 또는 환경 변수에 다음 설정을 추가하세요:")
        print("   telegram:")
        print("     bot_token: 'YOUR_BOT_TOKEN'")
        print("     chat_id: 'YOUR_CHAT_ID'")
        return
    
    print("[OK] 텔레그램 알림이 활성화되어 있습니다.")
    print()
    
    # 1. 일반 메시지 테스트
    print("1. 일반 메시지 전송 테스트...")
    try:
        result = await notifier.send_message("텔레그램 알림 테스트\n\n일반 메시지 전송 테스트입니다.")
        if result:
            print("   [OK] 일반 메시지 전송 성공")
        else:
            print("   [X] 일반 메시지 전송 실패")
    except Exception as e:
        print(f"   [X] 오류 발생: {e}")
    print()
    
    await asyncio.sleep(1)
    
    # 2. 성공 알림 테스트
    print("2. 성공 알림 테스트...")
    try:
        result = await notifier.send_success(
            "테스트 성공",
            "텔레그램 성공 알림 테스트입니다.\n이 메시지가 보이면 성공적으로 전송된 것입니다."
        )
        if result:
            print("   [OK] 성공 알림 전송 성공")
        else:
            print("   [X] 성공 알림 전송 실패")
    except Exception as e:
        print(f"   [X] 오류 발생: {e}")
    print()
    
    await asyncio.sleep(1)
    
    # 3. 정보 알림 테스트
    print("3. 정보 알림 테스트...")
    try:
        result = await notifier.send_info(
            "시스템 정보",
            "텔레그램 정보 알림 테스트입니다.\n\n- 시스템 상태: 정상\n- 알림 기능: 활성화"
        )
        if result:
            print("   [OK] 정보 알림 전송 성공")
        else:
            print("   [X] 정보 알림 전송 실패")
    except Exception as e:
        print(f"   [X] 오류 발생: {e}")
    print()
    
    await asyncio.sleep(1)
    
    # 4. 에러 알림 테스트
    print("4. 에러 알림 테스트...")
    try:
        result = await notifier.send_error(
            "테스트 에러 메시지입니다.",
            "TestError",
            "텔레그램 에러 알림 테스트"
        )
        if result:
            print("   [OK] 에러 알림 전송 성공")
        else:
            print("   [X] 에러 알림 전송 실패")
    except Exception as e:
        print(f"   [X] 오류 발생: {e}")
    print()
    
    await asyncio.sleep(1)
    
    # 5. 주문 체결 알림 테스트 (실제 사용 예시)
    print("5. 주문 체결 알림 테스트...")
    try:
        result = await notifier.send_success(
            "주문 체결",
            "주문 체결: 005930 매수 10주 @ 70,000원"
        )
        if result:
            print("   [OK] 주문 체결 알림 전송 성공")
        else:
            print("   [X] 주문 체결 알림 전송 실패")
    except Exception as e:
        print(f"   [X] 오류 발생: {e}")
    print()
    
    print("=" * 60)
    print("텔레그램 알림 테스트 완료")
    print("=" * 60)
    print()
    print("팁:")
    print("   - 텔레그램 봇 토큰은 @BotFather에서 발급받을 수 있습니다.")
    print("   - 채팅 ID는 @userinfobot 또는 @getidsbot으로 확인할 수 있습니다.")
    print("   - 그룹 채팅의 경우 봇을 그룹에 추가한 후 채팅 ID를 확인하세요.")


if __name__ == "__main__":
    try:
        asyncio.run(test_telegram())
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}", exc_info=True)

