import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CongestionBadge from "../components/CongestionBadge.jsx";
import DataBadge from "../components/DataBadge.jsx";
import useFetch from "../hooks/useFetch.js";
import { useAuth } from "../hooks/useAuth.jsx";
import {
  deleteJob, errMsg, getCameras, getDatasets, getJobResults, getJobVideoUrl, getJobs,
  registerLocalVideo, reprocessJob, uploadVideo,
} from "../services/api.js";

export default function Process() {
  const { isAdmin } = useAuth();
  const cams = useFetch(() => getCameras());
  const dsets = useFetch(getDatasets);
  const jobs = useFetch(getJobs);
  const [file, setFile] = useState(null);
  const [localPath, setLocalPath] = useState("");
  const [form, setForm] = useState({ camera_id: "", dataset_id: "", recorded_at: "", line_ratio: 0.6 });
  const [msg, setMsg] = useState(null);
  const [uploadPct, setUploadPct] = useState(null);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  // keep refreshing the job list while anything is queued or processing
  const busy = (jobs.data || []).some((j) => j.status === "queued" || j.status === "processing");
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(jobs.reload, 3000);
    return () => clearInterval(t);
  }, [busy, jobs.reload]);

  // load the results of the selected job once it is done
  const selectedJob = (jobs.data || []).find((j) => j.id === selected);
  const selectedDone = selectedJob?.status === "done";
  useEffect(() => {
    setResult(null);
    setVideoUrl(null);
    if (!selected || !selectedDone) return;
    let url;
    getJobResults(selected).then(setResult).catch((e) => setMsg({ ok: false, text: errMsg(e) }));
    if (selectedJob?.has_output) getJobVideoUrl(selected).then((u) => { url = u; setVideoUrl(u); }).catch(() => {});
    return () => { if (url) URL.revokeObjectURL(url); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, selectedDone]);

  function common() {
    const base = { camera_id: Number(form.camera_id), line_ratio: Number(form.line_ratio) };
    if (form.dataset_id) base.dataset_id = Number(form.dataset_id);
    if (form.recorded_at) base.recorded_at = new Date(form.recorded_at).toISOString();
    return base;
  }

  async function submitUpload(e) {
    e.preventDefault();
    if (!file) return setMsg({ ok: false, text: "Choose a video file first" });
    const fd = new FormData();
    fd.append("file", file);
    const c = common();
    Object.entries(c).forEach(([k, v]) => fd.append(k, v));
    setUploadPct(0);
    try {
      const job = await uploadVideo(fd, (p) => setUploadPct(Math.round((p.loaded / (p.total || p.loaded)) * 100)));
      setMsg({ ok: true, text: `Video uploaded. Processing started (job ${job.id}).` });
      setFile(null);
      setSelected(job.id);
      jobs.reload();
    } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
    finally { setUploadPct(null); }
  }

  async function submitLocal(e) {
    e.preventDefault();
    try {
      const job = await registerLocalVideo({ ...common(), relative_path: localPath });
      setMsg({ ok: true, text: `Processing started (job ${job.id}).` });
      setSelected(job.id);
      jobs.reload();
    } catch (err) { setMsg({ ok: false, text: errMsg(err) }); }
  }

  const camName = (id) => (cams.data || []).find((c) => c.id === id)?.camera_code || id;
  const timeline = (result?.timeline || []).map((t, i) => ({ ...t, label: `#${i + 1}` }));

  return (
    <>
      <h1 className="page-title">Upload and process video</h1>
      <p className="page-sub">The AI detects, tracks and counts vehicles. A vehicle is counted once, when it crosses the red line. Processing runs in the background; CPU-only machines can be slow on long videos.</p>
      {msg && <div className={`alert ${msg.ok ? "alert-success" : "alert-danger"} py-2`}>{msg.text}</div>}

      {isAdmin ? (
        <div className="panel">
          <h3>Settings for the next video</h3>
          <div className="row g-2 mb-3">
            <div className="col-md-4"><label className="form-label">Camera</label>
              <select className="form-select" value={form.camera_id} onChange={(e) => setForm({ ...form, camera_id: e.target.value })}>
                <option value="">Choose...</option>{(cams.data || []).map((c) => <option key={c.id} value={c.id}>{c.camera_code} - {c.name} ({c.source_type})</option>)}</select></div>
            <div className="col-md-4"><label className="form-label">Dataset (optional)</label>
              <select className="form-select" value={form.dataset_id} onChange={(e) => setForm({ ...form, dataset_id: e.target.value })}>
                <option value="">None</option>{(dsets.data || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
            <div className="col-md-4"><label className="form-label">Video start time (optional)</label>
              <input className="form-control" type="datetime-local" value={form.recorded_at} onChange={(e) => setForm({ ...form, recorded_at: e.target.value })} /></div>
            <div className="col-md-6"><label className="form-label">Counting line position: {Math.round(form.line_ratio * 100)}% from the top</label>
              <input className="form-range" type="range" min="0.1" max="0.9" step="0.05" value={form.line_ratio} onChange={(e) => setForm({ ...form, line_ratio: e.target.value })} /></div>
          </div>
          <div className="row g-3">
            <form className="col-lg-6" onSubmit={submitUpload}>
              <label className="form-label">Upload a video file</label>
              <input className="form-control mb-2" type="file" accept="video/*" onChange={(e) => setFile(e.target.files[0] || null)} />
              <button className="btn btn-primary" disabled={!form.camera_id || uploadPct !== null}>{uploadPct !== null ? `Uploading ${uploadPct}%` : "Upload and process"}</button>
            </form>
            <form className="col-lg-6" onSubmit={submitLocal}>
              <label className="form-label">Or use a file already in datasets/raw_videos</label>
              <input className="form-control mb-2" placeholder="ua_detrac/MVI_20011.mp4" value={localPath} onChange={(e) => setLocalPath(e.target.value)} />
              <button className="btn btn-outline-primary" disabled={!form.camera_id || !localPath}>Process this file</button>
            </form>
          </div>
        </div>
      ) : <div className="alert alert-secondary">Only admins can upload videos. You can view the results below.</div>}

      <div className="panel">
        <h3>Processing history</h3>
        {(jobs.data || []).length === 0 ? <div className="empty">No videos processed yet.</div> : (
          <div className="table-wrap"><table className="tbl">
            <thead><tr><th>Job</th><th>File</th><th>Camera</th><th>Data</th><th>Status</th><th>Progress</th><th>Created</th>{isAdmin && <th />}</tr></thead>
            <tbody>{jobs.data.map((j) => (
              <tr key={j.id} className={`clickable ${selected === j.id ? "sel" : ""}`} onClick={() => setSelected(j.id)}>
                <td>{j.id}</td><td>{j.original_filename}</td><td>{camName(j.camera_id)}</td><td><DataBadge label={j.data_label} /></td>
                <td><span className={`status ${j.status}`}>{j.status}</span>{j.error && <div className="text-danger small">{j.error}</div>}</td>
                <td><div className="progress-slim"><div style={{ width: `${Math.round(j.progress * 100)}%` }} /></div></td>
                <td>{new Date(j.created_at).toLocaleString()}</td>
                {isAdmin && <td onClick={(e) => e.stopPropagation()}>
                  <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => reprocessJob(j.id).then(jobs.reload).catch((e) => setMsg({ ok: false, text: errMsg(e) }))}>Re-run</button>
                  <button className="btn btn-sm btn-outline-danger" onClick={() => window.confirm("Delete this job and its results?") && deleteJob(j.id).then(() => { setSelected(null); jobs.reload(); })}>Delete</button></td>}
              </tr>))}</tbody></table></div>
        )}
      </div>

      {selectedJob && (
        <div className="panel">
          <h3>Results for job {selectedJob.id}</h3>
          {!selectedDone && <div className="empty">{selectedJob.status === "failed" ? "This job failed. See the error in the table." : "Still processing..."}</div>}
          {result && (
            <div className="row g-3">
              <div className="col-lg-6 video-box">
                {videoUrl ? <video src={videoUrl} controls /> : <div className="empty">Processed video not available</div>}
              </div>
              <div className="col-lg-6">
                <p><strong>{result.total_vehicles}</strong> vehicles counted
                  {Object.entries(result.by_type).map(([t, n]) => <span key={t} className="ms-3">{t}: <strong>{n}</strong></span>)}</p>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={timeline}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" /><YAxis allowDecimals={false} /><Tooltip />
                    <Bar dataKey="total_count" name="Vehicles per period" fill="#2467c9" /></BarChart>
                </ResponsiveContainer>
                <div className="table-wrap"><table className="tbl"><thead><tr><th>Period</th><th>Vehicles</th><th>Flow / min</th><th>Density</th><th>Congestion</th></tr></thead>
                  <tbody>{timeline.map((t) => (<tr key={t.label}><td>{new Date(t.bucket_start).toLocaleString()}</td><td>{t.total_count}</td><td>{t.flow_per_min}</td><td>{t.density_index}</td><td><CongestionBadge level={t.level} /></td></tr>))}</tbody></table></div>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
