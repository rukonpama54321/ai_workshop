import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

interface QueueItem {
  id: string;
  status: string;
  total_claimable: number;
  claim_type: string | null;
}

export default function ReviewPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);

  useEffect(() => {
    api<QueueItem[]>("/review/queue").then(setQueue).catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Review queue</h1>
      {queue.length === 0 ? (
        <p className="text-slate-500">No claims pending review.</p>
      ) : (
        <ul className="space-y-2">
          {queue.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3 shadow-sm">
              <div>
                <span className="font-medium">{item.claim_type || "claim"}</span>
                <span className="ml-2 text-sm text-slate-500">{item.status.replace(/_/g, " ")}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-teal-800">₹{item.total_claimable.toLocaleString()} claimable</span>
                <Link to={`/claims/${item.id}`} className="text-teal-700 hover:underline">
                  Review →
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
