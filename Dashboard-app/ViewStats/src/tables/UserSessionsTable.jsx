import React, { useState } from "react";
import { fetchUserSessions } from "../api";

export default function UserSessionsTable() {
  const [userId, setUserId] = useState("");
  const [data, setData] = useState(null);

  const load = async () => {
    setData(await fetchUserSessions(userId));
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">🧑 User Sessions (5 min)</h2>

      <div className="flex gap-2 mb-4">
        <input
          value={userId}
          onChange={e => setUserId(e.target.value)}
          placeholder="Enter user_id"
          className="border p-2 rounded"
        />
        <button
          onClick={load}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          Load
        </button>
      </div>

      {data && (
        <table className="w-full border rounded-lg">
          <thead className="bg-gray-100">
            <tr>
              <th className="p-3 text-left">Session ID</th>
              <th className="p-3 text-left">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {data.sessions.map(s => (
              <tr key={s.session_id}>
                <td className="p-3 border-b">{s.session_id}</td>
                <td className="p-3 border-b">{s.last_seen}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
