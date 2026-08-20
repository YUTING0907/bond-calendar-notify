from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DATA_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
BEIJING_TIMEZONE = ZoneInfo("Asia/Shanghai")
REQUEST_TIMEOUT = (5, 20)


def build_session() -> requests.Session:
    """Build an HTTP session that retries transient read-only requests."""
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update({"User-Agent": "bond-calendar-notify/1.0"})
    session.mount("https://", adapter)
    return session


def get_bond_calendar(session: requests.Session | None = None) -> list[dict[str, Any]]:
    """Fetch the latest convertible-bond calendar from Eastmoney."""
    params = {
        "sortColumns": "PUBLIC_START_DATE,SECURITY_CODE",
        "sortTypes": "-1,-1",
        "pageSize": "50",
        "pageNumber": "1",
        "reportName": "RPT_BOND_CB_LIST",
        "columns": "ALL",
        "quoteType": "0",
        "source": "WEB",
        "client": "WEB",
    }
    client = session or build_session()
    response = client.get(DATA_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("东方财富接口没有返回有效 JSON") from exc

    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, dict):
        raise RuntimeError("东方财富接口响应缺少 result 字段")

    bonds = result.get("data")
    if not isinstance(bonds, list):
        raise RuntimeError("东方财富接口的 result.data 不是列表")

    print(f"已获取 {len(bonds)} 条可转债记录")
    return bonds


def get_today_date(now: datetime | None = None) -> str:
    """Return today's date in the Asia/Shanghai timezone."""
    current = now or datetime.now(BEIJING_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BEIJING_TIMEZONE)
    else:
        current = current.astimezone(BEIJING_TIMEZONE)
    return current.strftime("%Y-%m-%d")


def bonds_for_date(
    bonds: list[dict[str, Any]], target_date: str
) -> list[dict[str, Any]]:
    """Select bonds whose public subscription date matches target_date."""
    selected = []
    for bond in bonds:
        public_start_date = bond.get("PUBLIC_START_DATE")
        if public_start_date and str(public_start_date).split()[0] == target_date:
            selected.append(bond)
    return selected


def build_message(bonds: list[dict[str, Any]]) -> tuple[str, str]:
    if not bonds:
        return "📅 今日无可申购新债", "今天没有可申购的新债。"

    title = "📅 今日可申购新债"
    content = "\n".join(
        (
            f"🔹 **{bond.get('SECURITY_NAME_ABBR', '-')}**"
            f"（{bond.get('SECURITY_CODE', '-')}）"
            f" - 申购日期: {bond.get('PUBLIC_START_DATE', '-')}"
            f" - 信用评级: {bond.get('RATING', '-')}"
        )
        for bond in bonds
    )
    return title, content


def send_to_wechat(
    bonds: list[dict[str, Any]],
    *,
    server_key: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Send a ServerChan notification and fail on rejected responses."""
    key = server_key if server_key is not None else os.getenv("SERVERCHAN_API_KEY")
    if not key:
        raise RuntimeError("未设置 SERVERCHAN_API_KEY")

    title, content = build_message(bonds)
    client = session or build_session()
    response = client.post(
        f"https://sctapi.ftqq.com/{key}.send",
        data={"title": title, "desp": content},
        timeout=REQUEST_TIMEOUT,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError:
        # Do not include the request URL in the exception because it contains SendKey.
        raise RuntimeError(
            f"Server 酱 HTTP 请求失败（status={response.status_code}）"
        ) from None

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError("Server 酱没有返回有效 JSON") from exc

    if not isinstance(result, dict):
        raise RuntimeError("Server 酱返回了无法识别的响应")

    result_code = result.get("code", result.get("errno"))
    if result_code is not None and str(result_code) != "0":
        message = result.get("message", result.get("errmsg", "未知错误"))
        raise RuntimeError(f"Server 酱推送失败：{message}（code={result_code}）")

    print("Server 酱推送成功")
    return result


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} 必须是 true 或 false")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="查询今日可申购新债并通过 Server 酱推送")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只抓取并显示结果，不发送 Server 酱通知",
    )
    args = parser.parse_args(argv)

    today = get_today_date()
    bonds = get_bond_calendar()
    bonds_to_send = bonds_for_date(bonds, today)
    print(f"北京时间 {today}，找到 {len(bonds_to_send)} 只可申购新债")

    if args.dry_run:
        for bond in bonds_to_send:
            print(
                f"- {bond.get('SECURITY_NAME_ABBR', '-')}"
                f" ({bond.get('SECURITY_CODE', '-')})"
            )
        print("dry-run 完成，未发送微信通知")
        return 0

    if bonds_to_send or env_flag("NOTIFY_WHEN_EMPTY"):
        send_to_wechat(bonds_to_send)
    else:
        print("今日无可申购新债，按当前配置不发送通知")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
