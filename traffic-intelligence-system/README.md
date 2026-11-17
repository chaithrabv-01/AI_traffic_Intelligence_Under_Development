# Traffic Intelligence System

Upload traffic videos, detect / classify / track / count vehicles with YOLOv8 + ByteTrack, store results in
PostgreSQL + PostGIS, and explore them in a React dashboard.

> **Status:** written without being able to run Docker, pip or npm in the build environment. Python files were
> syntax-checked only. Expect to fix a small error or two on first run. Follow "Fix errors" below.

## 1. Run it

1. Install Docker Desktop. Copy `.env.example` to `.env` and change the passwords.
2. `docker compose up --build` (first build downloads PyTorch, so it takes a while).
3. Open http://localhost:5173 and log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env`.
4. API docs: http://localhost:8000/docs  Health check: http://localhost:8000/health

First YOLO run downloads `yolov8n.pt` automatically (needs internet). To avoid that, put the file in `models/`.

## 2. First end-to-end test
1. **Locations**: add a location (name, city, latitude, longitude), then a camera for it.
   Use data type **Sample (demo)** unless the footage truly comes from that place.
2. **Upload & process**: choose the camera, pick a short video (10-30 s first), click *Upload and process*.
3. Watch status change `queued -> processing -> done`. Click the row to see the annotated video, counts and density.
4. **Dashboard / Compare / History** now show real numbers computed from that video.

## 3. How the files connect

| Step | File | What happens |
|---|---|---|
| Services start | `docker-compose.yml` | Starts `db` (PostGIS), waits until healthy, starts `backend` and `frontend`. `.env` feeds all three. |
| Config | `backend/app/core/config.py` | Reads environment variables (`DATABASE_URL`, thresholds, paths). |
| DB connection | `backend/app/database/session.py` | Builds the SQLAlchemy engine, `SessionLocal`, `Base`, and `get_db()`. |
| Tables | `backend/app/models/*.py` | Classes inheriting `Base`; `models/__init__.py` imports them all. |
| Start-up | `backend/app/main.py` | Enables PostGIS, creates tables, seeds admin, mounts routers under `/api`. |
| Routes | `backend/app/api/*.py` | `auth`, `locations` (+cameras), `datasets`, `videos`, `traffic`. Each file has a `router` that `main.py` includes. |
| Upload -> AI | `api/videos.py` -> `services/video_processing.run_job` | Upload saves the file, creates a `video_jobs` row, queues `run_job` as a FastAPI background task. |
| AI | `app/ai/detector.py` | YOLO + ByteTrack + line counting. Pure Python, no database. Returns a `VideoResult`. |
| Save results | `services/video_processing.py` | Writes `vehicle_detections`, `vehicle_counts`, `traffic_stats`, `congestion_records`. |
| Formulas | `services/traffic_metrics.py` | Density, flow, congestion level. Edit thresholds here / in `.env`. |
| Analytics | `services/traffic_analysis.py` -> `api/traffic.py` | SQL aggregation for dashboards. |
| Frontend -> API | `frontend/src/services/api.js` | The only place that calls the backend (`VITE_API_URL`). Adds the login token. |
| Pages | `frontend/src/pages/*.jsx` | Call functions from `api.js` through `hooks/useFetch.js`. `App.jsx` holds the routes. |

Flow of one video: **browser upload -> `POST /api/videos/upload` -> file in `datasets/raw_videos` + job row -> background
`run_job` -> `detector.process_video` -> rows in PostgreSQL + `datasets/processed_videos/job_N.mp4` ->
frontend polls `GET /api/videos` -> `GET /api/videos/N/results` and `/video`.**

## 4. Database tables
`users`, `locations` (PostGIS `geom` point), `cameras` (-> locations), `datasets` (-> locations, optional),
`video_jobs` (-> cameras, datasets, users), `vehicle_detections`, `vehicle_counts`, `traffic_stats`,
`congestion_records` (all -> video_jobs, and counts/stats/congestion also -> cameras and locations).
Deleting a location or job cascades to its rows. `/api/locations/nearby` uses PostGIS `ST_DWithin`.

Migrations: tables are auto-created on start (`AUTO_CREATE_TABLES=true`). To switch to Alembic:
```
docker compose exec backend alembic revision --autogenerate -m "initial"
docker compose exec backend alembic upgrade head
```
then set `AUTO_CREATE_TABLES=false`. (For an existing database, `alembic stamp head` after generating the first revision.)

## 5. How it counts and measures
- **Detection:** YOLOv8n finds cars, motorcycles (`bike`), buses, trucks, bicycles (`other`).
- **Tracking:** ByteTrack gives each vehicle an ID across frames.
- **Counting:** a vehicle is counted once, the first time its centre crosses the red line (set the line position per upload).
- **PCU weights** (`ai/detector.py`): car 1, bike 0.5, bus 3, truck 3, other 0.3. Indicative; change if you have local guidance.
- **Density index** = total PCU of all vehicles seen, summed over frames in a time bucket, divided by the number of frames
  = average PCU in view. **Flow per minute** = line crossings / minutes of video in that bucket.
- **Congestion:** `<= 6` low, `<= 15` medium, otherwise high (`DENSITY_LOW_MAX`, `DENSITY_MEDIUM_MAX`).
  Thresholds depend on how wide the camera view is, so tune them per scene.

## 6. Honest limits
- **No speed, no live traffic.** Density comes from one camera view of the footage you uploaded. Nothing is "real-time"
  unless you feed it a live stream (not built).
- **Data labels.** Cameras are `real_cctv`, `dataset_footage`, `sample`, `simulated`. The dashboard shows
  Real camera / Dataset footage / **Demo data** badges everywhere. The API refuses to link a dataset with no verified
  location to a real-type camera.
- **Auto-rickshaws** are not a COCO class; YOLO will usually label them car/motorcycle. For Indian roads, fine-tune on an
  Indian-labelled dataset (not included).
- **Timestamps** are video start time (given at upload, default: now) plus position in the video.
- CPU processing is slow (a 1 min 25 fps clip can take minutes). Raise `FRAME_STRIDE` to 2 or 3 to go faster.
- Background tasks run inside the API process: a restart loses an in-progress job (use *Re-run*). For production use a queue (Celery/RQ).
- The login token is stored in browser localStorage and `SECRET_KEY` must be changed. Put HTTPS in front before real deployment.
- Not included: live RTSP streams, UTD19 CSV import, model fine-tuning, automated tests.

## 7. API summary (all under `/api`, token required except register/login)
`POST /auth/login` `POST /auth/register` `GET /auth/me` ·
`GET/POST /locations` `GET /locations/nearby` `DELETE /locations/{id}` `GET/POST /cameras` ·
`GET/POST /datasets` `PATCH/DELETE /datasets/{id}` ·
`POST /videos/upload` `POST /videos/register-local` `GET /videos` `GET /videos/{id}` `GET /videos/{id}/results`
`GET /videos/{id}/video` `POST /videos/{id}/reprocess` `DELETE /videos/{id}` ·
`GET /traffic/overview|locations|compare|peak-hours|density-by-hour|trends|congestion|history`

## 8. Fix errors
- `docker compose logs backend` / `logs frontend` show the real error. Send me the last 30 lines.
- Backend can't reach DB: check `.env` values match and `db` is healthy.
- Video won't play in the browser: ffmpeg conversion failed; check backend logs.
- Port 5432 busy: change the left side of `"5432:5432"` in `docker-compose.yml`.

## 9. Deploy
Same `docker-compose.yml` on a server; replace the frontend dev server with `npm run build` served by nginx, set
`VITE_API_URL`, `CORS_ORIGINS`, strong secrets, and HTTPS.
