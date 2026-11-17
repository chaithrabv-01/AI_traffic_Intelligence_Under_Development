import { useState } from "react";
import DataBadge from "../components/DataBadge.jsx";
import TrafficMap from "../components/TrafficMap.jsx";
import useFetch from "../hooks/useFetch.js";
import { useAuth } from "../hooks/useAuth.jsx";
import { addCamera, addLocation, deleteLocation, errMsg, getCameras, getLocations } from "../services/api.js";

const SOURCE_LABEL = { real_cctv: "real", dataset_footage: "dataset", sample: "demo", simulated: "demo" };

export default function Locations() {
  const { isAdmin } = useAuth();
  const locs = useFetch(getLocations);
  const cams = useFetch(() => getCameras());
  const [msg, setMsg] = useState(null);
  const [loc, setLoc] = useState({ name: "", city: "", state: "", country: "India", latitude: "", longitude: "" });
  const [cam, setCam] = useState({ camera_code: "", name: "", location_id: "", source_type: "sample", description: "" });

  async function submitLoc(e) {
    e.preventDefault();
    try {
      await addLocation({ ...loc, state: loc.state || null, latitude: Number(loc.latitude), longitude: Number(loc.longitude) });
      setLoc({ name: "", city: "", state: "", country: "India", latitude: "", longitude: "" });
      setMsg({ ok: true, text: "Location added" });
      locs.reload();
    } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  async function submitCam(e) {
    e.preventDefault();
    try {
      await addCamera({ ...cam, location_id: Number(cam.location_id), description: cam.description || null });
      setCam({ camera_code: "", name: "", location_id: "", source_type: "sample", description: "" });
      setMsg({ ok: true, text: "Camera added" });
      cams.reload();
    } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  async function remove(id) {
    if (!window.confirm("Delete this location and everything recorded for it?")) return;
    try { await deleteLocation(id); locs.reload(); cams.reload(); } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  const list = locs.data || [];
  const mapPoints = list.map((l) => ({ ...l, location_id: l.id, total_vehicles: 0, latest_level: null, data_labels: [] }));

  return (
    <>
      <h1 className="page-title">Locations and cameras</h1>
      <p className="page-sub">A camera's source type says how honest its data is: real camera, dataset footage, or demo (sample or simulated).</p>
      {msg && <div className={`alert ${msg.ok ? "alert-success" : "alert-danger"} py-2`}>{msg.text}</div>}

      <div className="panel"><TrafficMap locations={mapPoints} /></div>

      <div className="panel">
        <h3>Locations</h3>
        {list.length === 0 ? <div className="empty">No locations yet.</div> : (
          <div className="table-wrap"><table className="tbl">
            <thead><tr><th>Name</th><th>City</th><th>State</th><th>Latitude</th><th>Longitude</th>{isAdmin && <th />}</tr></thead>
            <tbody>{list.map((l) => (
              <tr key={l.id}><td>{l.name}</td><td>{l.city}</td><td>{l.state || "-"}</td><td>{l.latitude}</td><td>{l.longitude}</td>
                {isAdmin && <td><button className="btn btn-sm btn-outline-danger" onClick={() => remove(l.id)}>Delete</button></td>}</tr>
            ))}</tbody></table></div>
        )}
      </div>

      <div className="panel">
        <h3>Cameras</h3>
        {(cams.data || []).length === 0 ? <div className="empty">No cameras yet.</div> : (
          <div className="table-wrap"><table className="tbl">
            <thead><tr><th>Camera ID</th><th>Name</th><th>Location</th><th>Data type</th></tr></thead>
            <tbody>{cams.data.map((c) => (
              <tr key={c.id}><td>{c.camera_code}</td><td>{c.name}</td>
                <td>{list.find((l) => l.id === c.location_id)?.name || c.location_id}</td>
                <td><DataBadge label={SOURCE_LABEL[c.source_type]} /> <span className="text-muted">{c.source_type}</span></td></tr>
            ))}</tbody></table></div>
        )}
      </div>

      {isAdmin && (
        <div className="row g-3">
          <div className="col-lg-6">
            <form className="panel" onSubmit={submitLoc}>
              <h3>Add a location</h3>
              <div className="row g-2">
                <div className="col-12"><label className="form-label">Name</label><input className="form-control" required value={loc.name} onChange={(e) => setLoc({ ...loc, name: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">City</label><input className="form-control" required value={loc.city} onChange={(e) => setLoc({ ...loc, city: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">State</label><input className="form-control" value={loc.state} onChange={(e) => setLoc({ ...loc, state: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">Latitude</label><input className="form-control" type="number" step="any" required value={loc.latitude} onChange={(e) => setLoc({ ...loc, latitude: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">Longitude</label><input className="form-control" type="number" step="any" required value={loc.longitude} onChange={(e) => setLoc({ ...loc, longitude: e.target.value })} /></div>
              </div>
              <button className="btn btn-primary mt-3">Add location</button>
            </form>
          </div>
          <div className="col-lg-6">
            <form className="panel" onSubmit={submitCam}>
              <h3>Add a camera</h3>
              <div className="row g-2">
                <div className="col-6"><label className="form-label">Camera ID</label><input className="form-control" required value={cam.camera_code} onChange={(e) => setCam({ ...cam, camera_code: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">Name</label><input className="form-control" required value={cam.name} onChange={(e) => setCam({ ...cam, name: e.target.value })} /></div>
                <div className="col-6"><label className="form-label">Location</label>
                  <select className="form-select" required value={cam.location_id} onChange={(e) => setCam({ ...cam, location_id: e.target.value })}>
                    <option value="">Choose...</option>{list.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                  </select></div>
                <div className="col-6"><label className="form-label">Data type</label>
                  <select className="form-select" value={cam.source_type} onChange={(e) => setCam({ ...cam, source_type: e.target.value })}>
                    <option value="real_cctv">Real CCTV at this location</option>
                    <option value="dataset_footage">Dataset footage recorded here</option>
                    <option value="sample">Sample (demo)</option>
                    <option value="simulated">Simulated (demo)</option>
                  </select></div>
                <div className="col-12"><label className="form-label">Description</label><input className="form-control" value={cam.description} onChange={(e) => setCam({ ...cam, description: e.target.value })} /></div>
              </div>
              <button className="btn btn-primary mt-3">Add camera</button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
