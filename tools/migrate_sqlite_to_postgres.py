#!/usr/bin/env python3
"""SQLite -> PostgreSQL(또는 임의의 SQLAlchemy DB) 데이터 이전 스크립트.

사용법:
  python tools/migrate_sqlite_to_postgres.py \
      --source sqlite:///app/data/inventory.db \
      --target "postgresql+psycopg2://user:pass@host:5432/inventory"

- 원본 DB 의 스키마를 읽어서(reflection) 대상 DB 에 같은 테이블을 만들고 모든 행을 복사합니다.
- 대상 테이블에 이미 데이터가 있으면 중단합니다 (--truncate 로 비우고 다시 복사 가능).
- PostgreSQL 은 id 를 직접 넣으면 시퀀스가 따라오지 않으므로, 복사 후 시퀀스를 맞춰 줍니다.
"""
import argparse
import sys

from sqlalchemy import MetaData, create_engine, inspect, select, text


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--source", required=True, help="원본 DB URL (예: sqlite:///app/data/inventory.db)")
    parser.add_argument("--target", required=True, help="대상 DB URL (예: postgresql+psycopg2://...)")
    parser.add_argument("--truncate", action="store_true", help="대상 테이블을 비우고 다시 복사")
    args = parser.parse_args()

    src_engine = create_engine(args.source)
    dst_engine = create_engine(args.target)

    src_meta = MetaData()
    src_meta.reflect(bind=src_engine)
    if not src_meta.tables:
        sys.exit("원본 DB 에 테이블이 없습니다. --source 경로를 확인하세요.")

    # SQLite 전용 타입(예: DATETIME)을 DB 중립 타입으로 바꿔서 대상 DB 에 맞는 DDL 이 생성되게 함
    for table in src_meta.tables.values():
        for col in table.columns:
            col.type = col.type.as_generic()

    # 원본 스키마를 대상 DB 에 생성 (이미 있으면 그대로 사용)
    src_meta.create_all(bind=dst_engine)

    with src_engine.connect() as src, dst_engine.begin() as dst:
        for table in src_meta.sorted_tables:
            existing = dst.execute(select(table).limit(1)).first()
            if existing:
                if not args.truncate:
                    sys.exit(f"대상 테이블 '{table.name}' 에 이미 데이터가 있습니다. 덮어쓰려면 --truncate 를 사용하세요.")
                dst.execute(table.delete())

            rows = [dict(r._mapping) for r in src.execute(select(table))]
            if rows:
                dst.execute(table.insert(), rows)
            print(f"  {table.name}: {len(rows)} rows copied")

            # PostgreSQL: SERIAL 시퀀스를 최대 id 로 맞춤
            if dst_engine.dialect.name == "postgresql":
                for col in table.primary_key.columns:
                    if col.autoincrement and rows:
                        dst.execute(
                            text(
                                f"SELECT setval(pg_get_serial_sequence('{table.name}', '{col.name}'), "
                                f"(SELECT MAX({col.name}) FROM {table.name}))"
                            )
                        )

    print("완료! 대상 DB 테이블:", ", ".join(inspect(dst_engine).get_table_names()))


if __name__ == "__main__":
    main()
