import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CongestionBadge from "../components/CongestionBadge.jsx";
import { DataBadges } from "../components/DataBadge.jsx";
import StatCard from "../components/StatCard.jsx";
import TrafficMap from "../components/TrafficMap.jsx";
import useFetch from "../hooks/useFetch.js";
import { getOverview, getTrends } from "../services/api.js";

const TYPE_COLORS = { car: "#2467c9", bike: "#2e9e6b", bus: "#d2433a", truck: "#d99a00", other: "#8a96a2" };

export default function Dashboard() {
  const ov = useFetch(getOverview);
  const tr = useFetch(() => getTrends("day"));

  if (ov.loading) return <p>Loading...</p>;
  if (ov.error) return <div className="alert alert-danger">{ov.error}</div>;
  const d = ov.data;

  const typeData = Object.entries(d.by_type).map(([type, count]) => ({ type, count }));
  const locData = d.locations.map((l) => ({ name: l.name, vehicles: l.total_vehicles }));
  const trendData = (tr.data || []).map((r) => ({ day: r.period.slice(0, 10), vehicles: r.vehicles }));
  const noData = d.total_vehicles === 0 && d.active_locations === 0;

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">Everything here is computed from videos you processed. Density is measured from one camera view; it is not vehicle speed or live city traffic.</p>

      {noData && (
        <div className="empty mb-4">
          No traffic data yet. <Link to="/locations">Add a location and camera</Link>, then{" "}
          <Link to="/process">upload a video</Link> to process it.
        </div>
      )}

      <div className="row g-3 mb-4">
        <div className="col-6 col-lg-3"><StatCard label="Vehicles counted" value={d.total_vehicles.toLocaleString()} hint="crossed a counting line" /></div>
        <div className="col-6 col-lg-3"><StatCard label="Active locations" value={`${d.active_locations} / ${d.locations_total}`} hint="locations with processed video" /></div>
        <div className="col-6 col-lg-3"><StatCard label="Current density" value={d.current_density ?? "-"} hint="average PCU in view, latest period" /></div>
        <div className="col-6 col-lg-3"><StatCard label="Congestion alerts" value={d.alerts.length} hint="locations at High" alert={d.alerts.length > 0} /></div>
      </div>

      {d.alerts.length > 0 && (
        <div className="panel">
          <h3>Congestion alerts</h3>
          {d.alerts.map((a) => (
            <div key={a.location_id} className="d-flex flex-wrap gap-3 align-items-center py-1">
              <CongestionBadge level="high" /> <strong>{a.name}</strong>
              <span className="text-muted">density {a.density}</span>
              <DataBadges labels={a.data_labels} />
              <span className="text-muted">{new Date(a.time).toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}

      <div className="panel">
        <h3>Map</h3>
        <TrafficMap locations={d.locations} />
      </div>

      <div className="row g-3">
        <div className="col-lg-6">
          <div className="panel">
            <h3>Vehicle categories</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="type" /><YAxis allowDecimals={false} /><Tooltip />
                <Bar dataKey="count" name="Vehicles">{typeData.map((t) => <Cell key={t.type} fill={TYPE_COLORS[t.type] || "#8a96a2"} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="panel">
            <h3>Vehicles by location</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={locData}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
                <Bar dataKey="vehicles" fill="#2467c9" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Daily trend</h3>
        {trendData.length === 0 ? <div className="empty">No data yet.</div> : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis allowDecimals={false} /><Tooltip />
              <Line type="monotone" dataKey="vehicles" stroke="#2467c9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="panel">
        <h3>Locations</h3>
        <div className="table-wrap">
          <table className="tbl">
            <thead><tr><th>Location</th><th>City</th><th>Vehicles</th><th>Avg density</th><th>Latest congestion</th><th>Data</th></tr></thead>
            <tbody>
              {d.locations.map((l) => (
                <tr key={l.location_id}>
                  <td>{l.name}</td><td>{l.city}{l.state ? `, ${l.state}` : ""}</td><td>{l.total_vehicles}</td>
                  <td>{l.avg_density ?? "-"}</td><td><CongestionBadge level={l.latest_level} /></td>
                  <td><DataBadges labels={l.data_labels} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
