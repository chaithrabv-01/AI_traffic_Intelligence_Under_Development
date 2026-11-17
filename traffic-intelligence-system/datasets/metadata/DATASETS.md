# Dataset guide

Only facts I could confirm are stated as facts. Everything else is marked **verify yourself**.
No download links are invented here: open the official page, read the licence, then download.

## Rule for this project
A dataset is tied to a real place **only if its own documentation says it was recorded there**.
Otherwise use a camera with source type `sample` and the data is shown as **Demo data** in the dashboard.

## 1. UA-DETRAC (video, vehicle detection and tracking)
- **Confirmed:** 100 videos of real-world traffic, over 140,000 frames, about 1.21 million labelled vehicle boxes
  (paper: arXiv 1511.04136, Wen et al., Computer Vision and Image Understanding, 2020).
- **Where recorded:** not India. The authors are from US/China institutions; my recollection is that the footage is from
  China (verify in the paper's dataset section before writing it into the Datasets page).
- **Use here:** testing the detector and counter on real road video. Register it with *no verified location*,
  and attach videos to a **sample** camera (shows as Demo data).
- **Download / licence:** **verify yourself.** Follow the dataset link in the paper (arxiv.org/abs/1511.04136) and read
  the terms there. I could not confirm the current hosting or licence text.
- **Organise:** `datasets/raw_videos/ua_detrac/<video>.mp4` (convert image sequences to mp4 with ffmpeg if needed),
  then use *Upload and process -> Or use a file already in datasets/raw_videos* with `ua_detrac/<video>.mp4`.

## 2. UTD19 (detector data, not video)
- **Confirmed:** ETH Zurich, Institute for Transport Planning and Systems. Loop-detector measurements (flow, and
  occupancy or speed) in 3-5 minute intervals from 40 cities, about 23,500 detectors, detectors geo-coded in WGS84.
- **Page:** https://utd19.ethz.ch/ (free, you must sign up and accept the conditions).
  Archive record: https://doi.org/10.3929/ethz-b-000437802
- **Licence:** CC BY-NC-SA 4.0 (non-commercial, share-alike). Size about 6.5 GB. Cite Loder et al. (2019),
  https://doi.org/10.1038/s41598-019-51539-5, and credit "UTD19 (utd19.ethz.ch)".
- **Cities:** check the city list on the site. I have not confirmed that any Indian city is included.
- **Use here:** it has no vehicle video, so YOLO cannot use it. It is useful for a later CSV import module
  (real flow, occupancy and speed per detector). Not implemented in this zip.

## 3. Indian traffic datasets (ITD, MTID and others)
- **Not verified.** I could not confirm exact names, contents, sizes or licences for "ITD" or "MTID".
- Search Kaggle, GitHub and Google Scholar for "Indian traffic dataset" or "Indian vehicle detection", then record
  for each: owner, licence, where and when it was recorded, whether it is video or images.
- Many Indian datasets contain still images (useful for fine-tuning, not for counting). Only video can be processed here.
- Your own phone or CCTV footage from a known junction is the most reliable way to get a genuinely Indian,
  genuinely located camera: add the location, create a `real_cctv` camera, upload the video.

## Folder layout
```
datasets/
  raw_videos/<dataset_name>/...   videos the backend reads
  processed_videos/               annotated output videos (written by the backend)
  images/<dataset_name>/...       still-image datasets (for later training)
  metadata/                       notes, licence copies, this file
```
