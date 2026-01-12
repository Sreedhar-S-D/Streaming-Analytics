class RedisRebuilder:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.conn = psycopg2.connect(
            dbname="analytics",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        self.cur = self.conn.cursor()

    def rebuild(self):
        print("Rebuilding Redis from TimescaleDB...")

        self.r.flushdb()

        # 1. Active users (last 5 min)
        self.cur.execute("""
            SELECT user_id, COUNT(*)
            FROM events
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
            GROUP BY user_id
        """)
        for user_id, count in self.cur.fetchall():
            self.r.zadd("active_users:5m", {user_id: count})
        self.r.expire("active_users:5m", 300)

        # 2. Page views (last 15 min)
        self.cur.execute("""
            SELECT page_url, COUNT(*)
            FROM events
            WHERE timestamp > NOW() - INTERVAL '15 minutes'
            GROUP BY page_url
        """)
        for url, count in self.cur.fetchall():
            self.r.zadd("page_views:15m", {url: count})
        self.r.expire("page_views:15m", 900)

        # 3. Active sessions (last 5 min)
        self.cur.execute("""
            SELECT user_id, session_id, MAX(timestamp)
            FROM events
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
            GROUP BY user_id, session_id
        """)
        for user_id, session_id, ts in self.cur.fetchall():
            key = f"sessions:{user_id}"
            self.r.hset(key, session_id, ts.isoformat())
            self.r.expire(key, 300)

        print("Redis rebuild complete")


if __name__ == "__main__":
    RedisRebuilder().rebuild()
