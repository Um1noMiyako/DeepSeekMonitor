"""DeepSeek API — GET /user/balance"""
from dataclasses import dataclass, field
from typing import Optional
import requests
import time


@dataclass
class BalanceInfo:
    currency: str
    total_balance: str
    granted_balance: str
    topped_up_balance: str


@dataclass
class Balance:
    is_available: bool
    balance_infos: list[BalanceInfo] = field(default_factory=list)
    response_time_ms: float = 0.0


@dataclass
class BalanceError:
    message: str
    status_code: Optional[int] = None


API_URL = "https://api.deepseek.com/user/balance"
TIMEOUT = (10, 15)  # (connect, read)


def fetch_balance(api_key: str) -> Balance | BalanceError:
    """调用 DeepSeek 余额 API，返回 Balance 或 BalanceError"""
    if not api_key:
        return BalanceError("未配置 API Key")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        t0 = time.perf_counter()
        resp = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
        elapsed = (time.perf_counter() - t0) * 1000

        if resp.status_code == 200:
            data = resp.json()
            infos = [BalanceInfo(
                currency=info.get("currency", ""),
                total_balance=info.get("total_balance", "0"),
                granted_balance=info.get("granted_balance", "0"),
                topped_up_balance=info.get("topped_up_balance", "0"),
            ) for info in data.get("balance_infos", [])]
            return Balance(
                is_available=data.get("is_available", False),
                balance_infos=infos,
                response_time_ms=elapsed,
            )

        if resp.status_code == 401:
            return BalanceError("API Key 无效，请在设置中更新", 401)
        elif resp.status_code == 429:
            return BalanceError("请求太频繁，请稍后重试", 429)
        else:
            return BalanceError(f"服务器错误 ({resp.status_code})", resp.status_code)

    except requests.exceptions.Timeout:
        return BalanceError("请求超时，请检查网络")
    except requests.exceptions.ConnectionError:
        return BalanceError("网络连接失败，请检查网络")
    except Exception as e:
        return BalanceError(f"未知错误: {e}")
