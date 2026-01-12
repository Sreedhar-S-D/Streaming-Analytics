const BASE_URL = "http://localhost:8000";

export async function fetchActiveUsers() {
  const res = await fetch(`${BASE_URL}/metrics/active-users`);
  return res.json();
}

export async function fetchPageViews() {
  const res = await fetch(`${BASE_URL}/metrics/page-views`);
  return res.json();
}

export async function fetchUserSessions(userId) {
  const res = await fetch(`${BASE_URL}/metrics/user-sessions/${userId}`);
  return res.json();
}
