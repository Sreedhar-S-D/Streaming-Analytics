import ActiveUsersTable from "./tables/ActiveUsersTable.jsx";
import PageViewsTable from "./tables/PageViewsTable.jsx";
import UserSessionsTable from "./tables/UserSessionsTable.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8 space-y-10">
      <h1 className="text-3xl font-bold text-center">
        📊 Real-Time Analytics Dashboard
      </h1>

      <ActiveUsersTable />
      <PageViewsTable />
      <UserSessionsTable />
    </div>
  );
}
