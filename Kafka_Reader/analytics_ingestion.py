import json
import asyncio
from datetime import datetime
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from kafka import KafkaConsumer
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import redis
from rate_limiter import BatchedBotValidator


KAFKA_BATCH_SIZE = 1000
DB_BATCH_SIZE = 500
REDIS_BATCH_SIZE = 500
DB_WORKERS = 4
REDIS_WORKERS = 4

consumer = KafkaConsumer(
    "events",
    bootstrap_servers="localhost:9092",
    group_id="analytics-consumer",
    auto_offset_reset="latest",
    enable_auto_commit=False,
    max_poll_records=KAFKA_BATCH_SIZE,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

db_pool = ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dbname="analytics",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432,
)


redis_pool = redis.ConnectionPool(
    host="localhost",
    port=6379,
    max_connections=20,
    decode_responses=True,
)

validator = BatchedBotValidator()


def write_db_batch(events):
    conn = db_pool.getconn()
    cur = conn.cursor()

    try:
        values = []
        for e in events:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", ""))
            values.append(
                (ts, e["user_id"], e["event_type"], e["page_url"], e["session_id"])
            )

        args = ",".join(
            cur.mogrify("(%s,%s,%s,%s,%s)", v).decode()
            for v in values
        )

        cur.execute(
            f"""
            INSERT INTO events
            (timestamp, user_id, event_type, page_url, session_id)
            VALUES {args}
            """
        )

        conn.commit()

    except Exception as ex:
        conn.rollback()
        print("DB ERROR:", ex)
        raise

    finally:
        db_pool.putconn(conn)


def write_redis_batch(events):
    r = redis.Redis(connection_pool=redis_pool)
    pipe = r.pipeline()

    try:
        for e in events:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", ""))
            user_id = e["user_id"]
            page_url = e["page_url"]
            session_id = e["session_id"]

            pipe.zincrby("active_users:5m", 1, user_id)
            pipe.expire("active_users:5m", 300)

            pipe.zincrby("page_views:15m", 1, page_url)
            pipe.expire("page_views:15m", 900)

            key = f"sessions:{user_id}"
            pipe.hset(key, session_id, ts.isoformat())
            pipe.expire(key, 300)

        pipe.execute()

    except Exception as ex:
        print("REDIS ERROR:", ex)
        raise


async def process_batches(loop, db_executor, redis_executor, validator):
    print("Ingestion started...")

    while True:
        records = consumer.poll(timeout_ms=1000)
        # print("records is", records)
        for tp, msgs in records.items():
            
            events = [msg.value for msg in msgs]

            if not events:
                continue
            
            valid_events = [e for e in events if validator.validate_event(e)]

            # STEP 1: Batched bot validation (ONCE per poll)
            allowed_events, bot_events = validator.validate_batch(valid_events)

            if not allowed_events:
                # still commit offsets, bots are intentionally dropped
                consumer.commit()
                continue

            # STEP 2: Split ONLY allowed events
            db_batches = [
                allowed_events[i:i + DB_BATCH_SIZE]
                for i in range(0, len(allowed_events), DB_BATCH_SIZE)
            ]

            redis_batches = [
                allowed_events[i:i + REDIS_BATCH_SIZE]
                for i in range(0, len(allowed_events), REDIS_BATCH_SIZE)
            ]

            # STEP 3: DB writes FIRST (source of truth)
            db_tasks = [
                loop.run_in_executor(db_executor, write_db_batch, batch)
                for batch in db_batches
            ]

            await asyncio.gather(*db_tasks)

            # STEP 4: Redis writes AFTER DB success
            redis_tasks = [
                loop.run_in_executor(redis_executor, write_redis_batch, batch)
                for batch in redis_batches
            ]

            await asyncio.gather(*redis_tasks)

            # ✅ STEP 5: commit Kafka offsets
            consumer.commit()


validator = BatchedBotValidator()
async def main():

    loop = asyncio.get_running_loop()
    db_executor = ThreadPoolExecutor(max_workers=DB_WORKERS)
    redis_executor = ThreadPoolExecutor(max_workers=REDIS_WORKERS)
    print("starting off now")
    await process_batches(loop, db_executor, redis_executor, validator)


if __name__ == "__main__":
    asyncio.run(main())


