#!/usr/bin/env python3
"""Simple HTTP load generator (standard library only, nothing to install).
간단한 HTTP 부하 생성기 (표준 라이브러리만 사용, 설치 불필요).

Usage / 사용법:
  python tools/loadtest.py https://<앱 FQDN> --duration 60 --concurrency 50

Collects "hostname" (= replica name) from the /health JSON and reports how many
replicas served the requests.
응답의 /health JSON 에서 hostname(= 레플리카 이름)을 수집해서,
요청이 몇 개의 레플리카에 분산되었는지 마지막에 보여줍니다.
"""
import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter


def worker(url, stop_at, hosts, counters, errors, lock):
    while time.monotonic() < stop_at:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                body = json.loads(resp.read().decode())
            if (
                not isinstance(body, dict)
                or body.get("status") != "ok"
                or not isinstance(body.get("hostname"), str)
                or not body["hostname"]
            ):
                raise ValueError("Invalid /health response: expected status=ok and hostname")
            with lock:
                counters["ok"] += 1
                hosts[body["hostname"]] += 1
        except (urllib.error.URLError, OSError, ValueError, UnicodeError) as exc:
            with lock:
                counters["error"] += 1
                errors[f"{type(exc).__name__}: {exc}"] += 1


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="e.g. https://ca-inventory.xxx.koreacentral.azurecontainerapps.io")
    parser.add_argument("--duration", type=positive_int, default=60, help="Duration in seconds / 부하 지속 시간(초)")
    parser.add_argument("--concurrency", type=positive_int, default=50, help="Concurrent requests / 동시 요청 수")
    args = parser.parse_args()

    url = args.base_url.rstrip("/") + "/health"
    stop_at = time.monotonic() + args.duration
    hosts, counters, errors, lock = Counter(), Counter(), Counter(), threading.Lock()

    print(f"Load testing {url} with {args.concurrency} concurrent requests for {args.duration}s / 부하 테스트 시작...")
    threads = [
        threading.Thread(target=worker, args=(url, stop_at, hosts, counters, errors, lock), daemon=True)
        for _ in range(args.concurrency)
    ]
    for t in threads:
        t.start()

    while time.monotonic() < stop_at:
        time.sleep(min(5, max(0, stop_at - time.monotonic())))
        with lock:
            print(f"  ok={counters['ok']} error={counters['error']} replicas_seen={len(hosts)}")
    for t in threads:
        t.join()

    print("\n=== Results / 결과 ===")
    print(f"Success / 성공 {counters['ok']}  Errors / 실패 {counters['error']}")
    print(f"Replicas that responded / 응답한 레플리카 수: {len(hosts)}")
    for host, count in hosts.most_common():
        print(f"  {host}: {count}")
    for error, count in errors.most_common(3):
        print(f"  {error} ({count})", file=sys.stderr)
    if counters["error"] or not counters["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
