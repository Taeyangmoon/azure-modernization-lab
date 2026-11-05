#!/usr/bin/env python3
"""간단한 HTTP 부하 생성기 (표준 라이브러리만 사용, 설치 불필요).

사용법:
  python tools/loadtest.py https://<앱 FQDN> --duration 60 --concurrency 50

응답의 /health JSON 에서 hostname(= 레플리카 이름)을 수집해서,
요청이 몇 개의 레플리카에 분산되었는지 마지막에 보여줍니다.
"""
import argparse
import json
import threading
import time
import urllib.request
from collections import Counter


def worker(url, stop_at, hosts, counters, lock):
    while time.time() < stop_at:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                body = json.loads(resp.read().decode())
            with lock:
                counters["ok"] += 1
                hosts[body.get("hostname", "?")] += 1
        except Exception:
            with lock:
                counters["error"] += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="예: https://ca-inventory.xxx.koreacentral.azurecontainerapps.io")
    parser.add_argument("--duration", type=int, default=60, help="부하 지속 시간(초)")
    parser.add_argument("--concurrency", type=int, default=50, help="동시 요청 수")
    args = parser.parse_args()

    url = args.base_url.rstrip("/") + "/health"
    stop_at = time.time() + args.duration
    hosts, counters, lock = Counter(), Counter(), threading.Lock()

    print(f"{url} 에 {args.concurrency} 동시 요청으로 {args.duration}초간 부하를 줍니다...")
    threads = [
        threading.Thread(target=worker, args=(url, stop_at, hosts, counters, lock), daemon=True)
        for _ in range(args.concurrency)
    ]
    for t in threads:
        t.start()

    while time.time() < stop_at:
        time.sleep(5)
        with lock:
            print(f"  ok={counters['ok']} error={counters['error']} replicas_seen={len(hosts)}")
    for t in threads:
        t.join()

    print("\n=== 결과 ===")
    print(f"성공 {counters['ok']} / 실패 {counters['error']}")
    print(f"응답한 레플리카 수: {len(hosts)}")
    for host, count in hosts.most_common():
        print(f"  {host}: {count}")


if __name__ == "__main__":
    main()
