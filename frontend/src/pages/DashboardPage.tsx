import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ClaimSummary } from "../api";

const statusColor: Record<string, string> = {
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  pending_review: "bg-amber-100 text-amber-800",
  pending_signoff: "bg-blue-100 text-blue-800",
};

export default function DashboardPage() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);

  useEffect(() => {
    api<ClaimSummary[]>("/claims").then(setClaims).catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">My Claims</h1>
      {claims.length === 0 ? (
        <p className="text-slate-500">No claims yet. Upload a medical bill to get started.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Claimed</th>
                <th className="px-4 py-3">Claimable</th>
                <th className="px-4 py-3">Deductions</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-xs ${statusColor[c.status] || "bg-slate-100"}`}>
                      {c.status.replace(/_/g, " ")}
                      {c.has_review_flags && " ⚠"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{c.claim_type || "—"}</td>
                  <td className="px-4 py-3">₹{c.total_claimed.toLocaleString()}</td>
                  <td className="px-4 py-3 font-medium text-teal-800">₹{c.total_claimable.toLocaleString()}</td>
                  <td className="px-4 py-3 text-red-700">₹{c.total_deductions.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <Link to={`/claims/${c.id}`} className="text-teal-700 hover:underline">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
