import redis
import psycopg2
from datetime import datetime
from collections import defaultdict
import re


BOT_THRESHOLD = 10
USER_ID_RE = re.compile(r"^usr_\d+$")
SESSION_ID_RE = re.compile(r"^sess_\d+$")
PAGE_URL_RE = re.compile(r"^/pages/[A-Za-z0-9.\-]+$")

ALLOWED_EVENT_TYPES = {"page_view"}

class BatchedBotValidator:
    def __init__(self,):
        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        self.pg = psycopg2.connect(
            dbname="botdb",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        self.cur = self.pg.cursor()
    
    def validate_event(self, event):
        try:
            # Required fields
            required = {
                "timestamp",
                "user_id",
                "event_type",
                "page_url",
                "session_id",
            }

            if not required.issubset(event.keys()):
                return False

            # Timestamp validation
            ts = event["timestamp"]

            if not isinstance(ts, str) or not ts.endswith("Z"):
                return False

            # ISO parse (supports milliseconds)
            datetime.fromisoformat(ts.replace("Z", "+00:00"))

            # ------------------------
            # user_id
            # ------------------------
            if not USER_ID_RE.match(event["user_id"]):
                return False

            # ------------------------
            # event_type
            # ------------------------
            if event["event_type"] not in ALLOWED_EVENT_TYPES:
                return False

            # ------------------------
            # page_url
            # ------------------------
            if not PAGE_URL_RE.match(event["page_url"]):
                return False

            # ------------------------
            # session_id
            # ------------------------
            if not SESSION_ID_RE.match(event["session_id"]):
                return False

            return True

        except Exception:
            # Fail fast & safe
            return False

    

    def validate_batch(self, events):
        """
        Returns:
        - allowed_events
        - bot_events
        """

        buckets = defaultdict(list)

        # 1. Group events by (user_id, time_bucket)
        for e in events:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", ""))
            bucket = ts.replace(microsecond=0)
            key = f"botcheck:{e['user_id']}:{bucket.isoformat()}"
            buckets[key].append((e["user_id"], bucket, e))

        # 2. Redis pipeline increment
        pipe = self.redis.pipeline()
        for key in buckets:
            pipe.incr(key)
            pipe.expire(key, 2)
        counts = pipe.execute()

        allowed = []
        bots = []
        offenders = []

        # 3. Decision
        for (key, count) in zip(buckets.keys(), counts[::2]):
            user_id, bucket, _ = buckets[key][0]

            if count <= BOT_THRESHOLD:
                allowed.extend(e for _, _, e in buckets[key])
            else:
                bots.extend(e for _, _, e in buckets[key])
                offenders.append((user_id, bucket, count))

        # 4. Persist bot stats (batch)
        if offenders:
            self._persist_bots(offenders)

        return allowed, bots

    def _persist_bots(self, offenders):
        try:
            self.cur.executemany("""
                INSERT INTO user_event_rate (user_id, time_bucket, event_count)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, time_bucket)
                DO UPDATE SET event_count = EXCLUDED.event_count
            """, offenders)

            self.cur.executemany("""
                INSERT INTO bot_users (user_id, reason)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, [(u, "Excessive parallel clicks") for u, _, _ in offenders])

            self.pg.commit()
        except Exception as e:
            self.pg.rollback()
            print("⚠️ Bot persistence failed:", e)

