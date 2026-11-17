import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CongestionBadge from "../components/CongestionBadge.jsx";
import DataBadge from "../components/DataBadge.jsx";
import useFetch from "../hooks/useFetch.js";
import { getDensityByHour, getHistory, getLocations, getPeakHours, getTrends } from "../services/api.js";

export default function History() {
  const locs = useFetch(getLocations);
  const [loc, setLoc] = useState("");
  const [gran, setGran] = useState("day");
  const lid = loc ? Number(loc) : undefined;

  const trend = useFetch(() => getTrends(gran, lid), [gran, loc]);
  const peak = useFetch(() => getPeakHours(lid), [loc]);
  const dens = useFetch(() => getDensityByHour(lid), [loc]);
  const hist = useFetch(() => getHistory({ location_id: lid, limit: 100 }), [loc]);

  const locName = (id) => (locs.data || []).find((l) => l.id === id)?.name || id;
  const trendData = (trend.data || []).map((r) => ({ period: gran === "hour" ? r.period.replace("T", " ").slice(0, 16) : r.period.slice(0, 10), vehicles: r.vehicles }));
  const peakData = (peak.data || []).map((p) => ({ hour: `${String(p.hour).padStart(2, "0")}h`, vehicles: p.vehicles }));
  const densData = (dens.data || []).map((p) => ({ hour: `${String(p.hour).padStart(2, "0")}h`, density: p.density }));
  const best = (peak.data || []).reduce((a, b) => (b.vehicles > (a?.vehicles ?? 0) ? b : a), null);

  return (
    <>
      <h1 className="page-title">Historical analysis</h1>
      <p className="page-sub">Hours are shown in Asia/Kolkata. The time of each record is the video start time you gave at upload, plus the position in the video.</p>

      <div className="panel d-flex flex-wrap gap-3 align-items-end">
        <div><label className="form-label">Location</label>
          <select className="form-select" value={loc} onChange={(e) => setLoc(e.target.value)}>
            <option value="">All locations</option>{(locs.data || []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}</select></div>
        <div><label className="form-label">Trend by</label>
          <select className="form-select" value={gran} onChange={(e) => setGran(e.target.value)}>
            <option value="hour">Hour</option><option value="day">Day</option><option value="week">Week</option></select></div>
      </div>

      <div className="panel"><h3>Vehicle trend</h3>
        {trendData.length === 0 ? <div className="empty">No data for this selection.</div> : (
          <ResponsiveContainer width="100%" height={260}><LineChart data={trendData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="period" /><YAxis allowDecimals={false} /><Tooltip />
            <Line type="monotone" dataKey="vehicles" stroke="#2467c9" strokeWidth={2} /></LineChart></ResponsiveContainer>)}</div>

      <div className="row g-3">
        <div className="col-lg-6"><div className="panel"><h3>Vehicles by hour of day {best && best.vehicles > 0 && <small className="text-muted">(peak {String(best.hour).padStart(2, "0")}:00)</small>}</h3>
          <ResponsiveContainer width="100%" height={240}><BarChart data={peakData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="hour" interval={2} /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="vehicles" fill="#2467c9" /></BarChart></ResponsiveContainer></div></div>
        <div className="col-lg-6"><div className="panel"><h3>Density by hour of day</h3>
          <ResponsiveContainer width="100%" height={240}><BarChart data={densData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="hour" interval={2} /><YAxis /><Tooltip /><Bar dataKey="density" fill="#d99a00" /></BarChart></ResponsiveContainer></div></div>
      </div>

      <div className="panel"><h3>Records</h3>
        {(hist.data || []).length === 0 ? <div className="empty">No records.</div> : (
          <div className="table-wrap"><table className="tbl">
            <thead><tr><th>Time</th><th>Location</th><th>Vehicles</th><th>Flow / min</th><th>Density</th><th>Congestion</th><th>Data</th></tr></thead>
            <tbody>{hist.data.map((r) => (
              <tr key={r.id}><td>{new Date(r.bucket_start).toLocaleString()}</td><td>{locName(r.location_id)}</td><td>{r.total_count}</td><td>{r.flow_per_min}</td><td>{r.density_index}</td>
                <td><CongestionBadge level={r.level} /></td><td><DataBadge label={r.data_label} /></td></tr>))}</tbody></table></div>)}</div>
    </>
  );
}
