import React, { useEffect, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from "@tanstack/react-table";
import { fetchActiveUsers } from "../api";

export default function ActiveUsersTable() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const load = async () => {
      setData(await fetchActiveUsers());
    };

    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  const columns = [
    {
      header: "User ID",
      accessorKey: "user_id",
    },
    {
      header: "Events (5 min)",
      accessorKey: "events",
    },
  ];

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">🔥 Active Users (5 min)</h2>
      <table className="w-full border rounded-lg">
        <thead className="bg-gray-100">
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id}>
              {hg.headers.map(h => (
                <th key={h.id} className="p-3 text-left border-b">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="hover:bg-gray-50">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="p-3 border-b">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
