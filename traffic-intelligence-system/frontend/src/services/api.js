// All calls to the FastAPI backend live here. Pages import these functions, never axios directly.
import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api" });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("tis_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      localStorage.removeItem("tis_token");
      localStorage.removeItem("tis_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function errMsg(e) {
  const d = e?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => `${x.loc?.slice(1).join(".")}: ${x.msg}`).join("; ");
  return e?.message || "Something went wrong";
}

const get = (url, params) => api.get(url, { params }).then((r) => r.data);
const post = (url, body, cfg) => api.post(url, body, cfg).then((r) => r.data);

export const login = (username, password) =>
  post("/auth/login", new URLSearchParams({ username, password }));

export const getOverview = () => get("/traffic/overview");
export const getLocationSummaries = () => get("/traffic/locations");
export const getCompare = (ids) => get("/traffic/compare", { location_ids: ids.join(",") });
export const getPeakHours = (location_id) => get("/traffic/peak-hours", { location_id });
export const getDensityByHour = (location_id) => get("/traffic/density-by-hour", { location_id });
export const getTrends = (granularity, location_id) => get("/traffic/trends", { granularity, location_id });
export const getCongestion = (params) => get("/traffic/congestion", params);
export const getHistory = (params) => get("/traffic/history", params);

export const getLocations = () => get("/locations");
export const addLocation = (body) => post("/locations", body);
export const deleteLocation = (id) => api.delete(`/locations/${id}`);
export const getCameras = (location_id) => get("/cameras", { location_id });
export const addCamera = (body) => post("/cameras", body);

export const getDatasets = () => get("/datasets");
export const addDataset = (body) => post("/datasets", body);
export const deleteDataset = (id) => api.delete(`/datasets/${id}`);

export const getJobs = () => get("/videos");
export const getJobResults = (id) => get(`/videos/${id}/results`);
export const uploadVideo = (formData, onUploadProgress) =>
  post("/videos/upload", formData, { onUploadProgress });
export const registerLocalVideo = (body) => post("/videos/register-local", body);
export const reprocessJob = (id) => post(`/videos/${id}/reprocess`);
export const deleteJob = (id) => api.delete(`/videos/${id}`);
// <video> tags cannot send the login token, so we download the file as a blob and play that.
export const getJobVideoUrl = (id) =>
  api.get(`/videos/${id}/video`, { responseType: "blob" }).then((r) => URL.createObjectURL(r.data));

export default api;
