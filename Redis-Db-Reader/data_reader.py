from fastapi import FastAPI, Query
import redis
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Real-time Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

# 1. Active Users (Last 5 Minutes)
@app.get("/metrics/active-users")
def get_active_users(limit: int = Query(10, ge=1, le=100)):
    """
    Top active users in last 5 minutes
    """
    users = r.zrevrange(
        "active_users:5m",
        0,
        limit - 1,
        withscores=True
    )

    return [
        {"user_id": user_id, "events": int(score)}
        for user_id, score in users
    ]


# 2. Page Views by URL (Last 15 Minutes)
@app.get("/metrics/page-views")
def get_page_views(limit: int = Query(10, ge=1, le=100)):
    """
    Most viewed pages in last 15 minutes
    """
    pages = r.zrevrange(
        "page_views:15m",
        0,
        limit - 1,
        withscores=True
    )

    return [
        {"page_url": url, "views": int(score)}
        for url, score in pages
    ]


# 3. Active Sessions for a User (Last 5 Minutes)
@app.get("/metrics/user-sessions/{user_id}")
def get_user_sessions(user_id: str):
    """
    Active sessions for a user in last 5 minutes
    """
    key = f"sessions:{user_id}"
    sessions = r.hgetall(key)

    return {
        "user_id": user_id,
        "active_sessions": len(sessions),
        "sessions": [
            {"session_id": sid, "last_seen": ts}
            for sid, ts in sessions.items()
        ]
    }
