import { useState } from "react";
import useFetch from "../hooks/useFetch.js";
import { useAuth } from "../hooks/useAuth.jsx";
import { addDataset, deleteDataset, errMsg, getDatasets, getLocations } from "../services/api.js";

const EMPTY = { name: "", source_url: "", license: "", data_type: "video", is_real_footage: true,
  source_location_note: "", location_id: "", local_path: "", notes: "" };

export default function Datasets() {
  const { isAdmin } = useAuth();
  const ds = useFetch(getDatasets);
  const locs = useFetch(getLocations);
  const [f, setF] = useState(EMPTY);
  const [msg, setMsg] = useState(null);

  async function submit(e) {
    e.preventDefault();
    const body = { ...f, location_id: f.location_id ? Number(f.location_id) : null };
    for (const k of ["source_url", "license", "source_location_note", "local_path", "notes"]) if (!body[k]) body[k] = null;
    try { await addDataset(body); setF(EMPTY); setMsg({ ok: true, text: "Dataset added" }); ds.reload(); }
    catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  async function remove(id) {
    if (!window.confirm("Delete this dataset record? Processed results stay.")) return;
    try { await deleteDataset(id); ds.reload(); } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  const locName = (id) => (locs.data || []).find((l) => l.id === id)?.name;

  return (
    <>
      <h1 className="page-title">Datasets</h1>
      <p className="page-sub">Record where each dataset came from, its licence and where it was really recorded. Put the files in <code>datasets/raw_videos/&lt;dataset-name&gt;/</code>.</p>
      {msg && <div className={`alert ${msg.ok ? "alert-success" : "alert-danger"} py-2`}>{msg.text}</div>}

      <div className="panel">
        {(ds.data || []).length === 0 ? <div className="empty">No datasets registered yet.</div> : (
          <div className="table-wrap"><table className="tbl">
            <thead><tr><th>Name</th><th>Type</th><th>Really recorded in</th><th>Verified location</th><th>Licence</th><th>Source</th>{isAdmin && <th />}</tr></thead>
            <tbody>{ds.data.map((d) => (
              <tr key={d.id}>
                <td>{d.name}</td><td>{d.data_type}</td><td>{d.source_location_note || <span className="text-muted">not stated</span>}</td>
                <td>{d.location_id ? locName(d.location_id) : <span className="text-muted">none (demo use only)</span>}</td>
                <td>{d.license || "-"}</td>
                <td>{d.source_url ? <a href={d.source_url} target="_blank" rel="noreferrer">link</a> : "-"}</td>
                {isAdmin && <td><button className="btn btn-sm btn-outline-danger" onClick={() => remove(d.id)}>Delete</button></td>}
              </tr>))}</tbody></table></div>
        )}
      </div>

      {isAdmin && (
        <form className="panel" onSubmit={submit}>
          <h3>Register a dataset</h3>
          <div className="row g-2">
            <div className="col-md-6"><label className="form-label">Name</label><input className="form-control" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
            <div className="col-md-6"><label className="form-label">Source URL</label><input className="form-control" value={f.source_url} onChange={(e) => setF({ ...f, source_url: e.target.value })} /></div>
            <div className="col-md-4"><label className="form-label">Licence</label><input className="form-control" value={f.license} onChange={(e) => setF({ ...f, license: e.target.value })} /></div>
            <div className="col-md-4"><label className="form-label">Type</label>
              <select className="form-select" value={f.data_type} onChange={(e) => setF({ ...f, data_type: e.target.value })}>
                <option value="video">Video</option><option value="images">Images</option><option value="csv">CSV / detector data</option></select></div>
            <div className="col-md-4"><label className="form-label">Local folder</label><input className="form-control" placeholder="raw_videos/ua_detrac" value={f.local_path} onChange={(e) => setF({ ...f, local_path: e.target.value })} /></div>
            <div className="col-12"><label className="form-label">Where was it really recorded?</label><input className="form-control" placeholder="Use the dataset's own documentation" value={f.source_location_note} onChange={(e) => setF({ ...f, source_location_note: e.target.value })} /></div>
            <div className="col-md-8"><label className="form-label">Verified location (optional)</label>
              <select className="form-select" value={f.location_id} onChange={(e) => setF({ ...f, location_id: e.target.value })}>
                <option value="">None - do not tie to a place</option>
                {(locs.data || []).map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}</select>
              <div className="form-text">Choose a location only if the dataset's own source says it was recorded there.</div></div>
            <div className="col-md-4 d-flex align-items-end"><div className="form-check">
              <input id="real" className="form-check-input" type="checkbox" checked={f.is_real_footage} onChange={(e) => setF({ ...f, is_real_footage: e.target.checked })} />
              <label htmlFor="real" className="form-check-label">Real footage</label></div></div>
          </div>
          <button className="btn btn-primary mt-3">Add dataset</button>
        </form>
      )}
    </>
  );
}
