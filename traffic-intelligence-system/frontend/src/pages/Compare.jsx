import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CongestionBadge from "../components/CongestionBadge.jsx";
import { DataBadges } from "../components/DataBadge.jsx";
import useFetch from "../hooks/useFetch.js";
import { getCompare, getLocations } from "../services/api.js";

export default function Compare() {
  const locs = useFetch(getLocations);
  const [ids, setIds] = useState([]);
  const cmp = useFetch(() => (ids.length ? getCompare(ids) : Promise.resolve([])), [ids.join(",")]);

  const toggle = (id) => setIds((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const rows = cmp.data || [];
  const chart = rows.map((r) => ({ name: r.name, Vehicles: r.total_vehicles, Density: r.avg_density || 0, "Flow per min": r.avg_flow_per_min || 0 }));
  const mixed = new Set(rows.flatMap((r) => r.data_labels));

  return (
    <>
      <h1 className="page-title">Compare locations</h1>
      <p className="page-sub">Pick two or more locations. Comparisons are only fair when the cameras see similar road widths and the footage covers similar time spans.</p>

      <div className="panel">
        <h3>Locations</h3>
        {(locs.data || []).length === 0 ? <div className="empty">No locations yet.</div> : (
          <div className="d-flex flex-wrap gap-3">
            {locs.data.map((l) => (
              <div className="form-check" key={l.id}>
                <input id={`l${l.id}`} className="form-check-input" type="checkbox" checked={ids.includes(l.id)} onChange={() => toggle(l.id)} />
                <label htmlFor={`l${l.id}`} className="form-check-label">{l.name}</label>
              </div>))}
          </div>
        )}
      </div>

      {ids.length > 0 && rows.length > 0 && (
        <>
          {mixed.size > 1 && <div className="alert alert-warning">These locations mix data types ({[...mixed].join(", ")}). Do not read demo or dataset figures as real conditions at the place.</div>}
          <div className="panel">
            <h3>Side by side</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="Vehicles" fill="#2467c9" /><Bar dataKey="Density" fill="#d99a00" /><Bar dataKey="Flow per min" fill="#2e9e6b" /></BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel"><div className="table-wrap"><table className="tbl">
            <thead><tr><th>Location</th><th>Vehicles</th><th>Avg density</th><th>Flow / min</th><th>Peak hour</th><th>Time at High</th><th>Latest</th><th>Data</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.location_id}><td>{r.name}</td><td>{r.total_vehicles}</td><td>{r.avg_density ?? "-"}</td><td>{r.avg_flow_per_min ?? "-"}</td>
                <td>{r.peak_hour != null ? `${String(r.peak_hour).padStart(2, "0")}:00` : "-"}</td><td>{r.pct_high}%</td>
                <td><CongestionBadge level={r.latest_level} /></td><td><DataBadges labels={r.data_labels} /></td></tr>))}</tbody></table></div></div>
        </>
      )}
    </>
  );
}
