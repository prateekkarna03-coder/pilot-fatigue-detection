# AI-Powered Human-Aware Pilot Safety & Fatigue Monitoring System

An intelligent, multimodal safety monitoring system designed for commercial and general aviation cockpits. The system combines real-time computer vision, temporal physiological feature extraction, machine learning classification, and large language model (LLM) advisory integration to detect early indicators of pilot fatigue, assess risk levels, and provide actionable operational recommendations.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Problem Statement and Objectives](#2-problem-statement-and-objectives)
- [3. System Architecture](#3-system-architecture)
- [4. System Architecture Diagram](#4-system-architecture-diagram)
- [5. Technology Stack](#5-technology-stack)
- [6. Major System Components](#6-major-system-components)
- [7. End-to-End Data Flow](#7-end-to-end-data-flow)
- [8. Computer Vision Pipeline](#8-computer-vision-pipeline)
  - [8.1 Video Ingestion & OpenCV Processing](#81-video-ingestion--opencv-processing)
  - [8.2 MediaPipe Face Landmarker](#82-mediapipe-face-landmarker)
  - [8.3 Geometric Feature Extraction (EAR, MAR, Head Pose)](#83-geometric-feature-extraction-ear-mar-head-pose)
  - [8.4 Temporal Feature Tracking & Signal Conditioning](#84-temporal-feature-tracking--signal-conditioning)
- [9. Machine Learning Pipeline](#9-machine-learning-pipeline)
  - [9.1 Dataset Preparation (UTA-RLDD)](#91-dataset-preparation-uta-rldd)
  - [9.2 Feature Vector Aggregation](#92-feature-vector-aggregation)
  - [9.3 Random Forest Classifier Pipeline](#93-random-forest-classifier-pipeline)
  - [9.4 Evaluation Methodology & Subject-Independent Validation](#94-evaluation-methodology--subject-independent-validation)
- [10. Risk Assessment and Scoring](#10-risk-assessment-and-scoring)
- [11. Real-Time WebSocket Communication](#11-real-time-websocket-communication)
- [12. Next.js Dashboard](#12-nextjs-dashboard)
- [13. API, Authentication, and Session Management](#13-api-authentication-and-session-management)
- [14. PostgreSQL Database and Prisma ORM](#14-postgresql-database-and-prisma-orm)
- [15. Gemini AI Recommendation Integration](#15-gemini-ai-recommendation-integration)
- [16. Security and Privacy Considerations](#16-security-and-privacy-considerations)
- [17. Model Evaluation Results](#17-model-evaluation-results)
- [18. Limitations and Future Improvements](#18-limitations-and-future-improvements)
- [19. Installation and Environment Setup](#19-installation-and-environment-setup)
- [20. How to Demonstrate the Project](#20-how-to-demonstrate-the-project)
- [21. Safety Disclaimer](#21-safety-disclaimer)
- [22. System Design Documentation (PDF)](#22-system-design-documentation-pdf)

---

## 1. Project Overview

The **AI-Powered Human-Aware Pilot Safety & Fatigue Monitoring System** is an engineering prototype developed as an academic semester project in Artificial Intelligence and Human-Computer Interaction. 

Fatigue is a leading contributory factor in aviation incidents and fatal accidents. Extended duty hours, circadian rhythm disruption, night flights, and cockpit monotony degrade pilot alertness, visual scanning vigilance, and cognitive reaction times.

This system addresses this critical aviation challenge by monitoring subtle physiological and behavioral markers in real time. It pairs a high-performance Python computer vision worker with a modern web-based command dashboard powered by Node.js, Next.js, PostgreSQL, and Google Gemini AI.

---

## 2. Problem Statement and Objectives

### Problem Statement
Pilot fatigue monitoring in modern flight operations relies heavily on static duty-time regulations and self-reporting surveys. However, individual sleep debt, circadian dips, and cockpit micro-environments create unannounced vigilance drops. Cockpit systems require non-intrusive, real-time sensing mechanisms capable of detecting physiological precursors to microsleeps before manual control or flight path management is compromised.

### Project Objectives
1. **Non-Intrusive Optical Sensing:** Track eye closure dynamics, yawn patterns, and 3D head pose orientation using non-contact RGB video streams.
2. **Robust Temporal Feature Extraction:** Mitigate natural facial motion artifacts (e.g., downward gaze during instrument checks) using dual-hysteresis thresholds and adaptive per-pilot baselines.
3. **Machine Learning Classification:** Train and evaluate an empirical classification model against validated academic fatigue datasets (Karolinska Sleepiness Scale ground truth).
4. **Deterministic Risk Assessment:** Compute standardized fatigue indices (0–100 scale) and risk tiers (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
5. **Low-Latency Cockpit Telemetry:** Stream telemetry over WebSockets to an interactive cockpit/analyst console with real-time metric charting and visual status displays.
6. **Context-Aware AI Advisory:** Employ LLM reasoning (Gemini Flash) to generate concise, operations-compliant corrective actions when critical risk thresholds are crossed.

---

## 3. System Architecture

The system is architected as two decoupled sub-systems connected via local inter-process communication and WebSocket protocols:

1. **Python Computer Vision Worker (`python-cv`):**
   - Captures real-time frames via OpenCV from a connected camera device.
   - Runs Google MediaPipe's dense 478-point 3D Face Landmarker task.
   - Extracts geometry (Eye Aspect Ratio, Mouth Aspect Ratio, 3D Head Pose via Perspective-n-Point / PnP).
   - Tracks temporal behavior (blinks, yawns, prolonged eyelid closure) across rolling time windows.
   - Buffers 10-second temporal feature vectors and computes inference via a Scikit-learn Random Forest classifier.
   - Transmits telemetry frames over local WebSockets to the web application.

2. **Next.js & Node.js Application Server (`server.js` + `src/`):**
   - Custom HTTP server running Next.js App Router and a co-located Node.js `ws` WebSocket server.
   - Manages pilot authentication and session lifecycles via NextAuth (Auth.js v4) and PostgreSQL / Prisma ORM.
   - Spawns and manages the Python worker child process bound to active flight monitoring sessions.
   - Broadcasts live telemetry to subscribed browser clients.
   - Validates incoming telemetry and persists time-series measurements (`FatigueMeasurement`, `RiskHistory`).
   - Invokes the Google Gemini AI recommendation engine when sustained high/critical risk is detected.

---

## 4. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Sensing["Optical Sensing & Vision Pipeline (Python Worker)"]
        Cam["Physical Camera / Video Capture"] --> Cap["OpenCV VideoCapture (30 FPS)"]
        Cap --> MP["MediaPipe Face Landmarker (478 3D Landmarks)"]
        MP --> Geom["Geometric Feature Extraction\n(EAR, MAR, solvePnP Head Pose)"]
        Geom --> Temp["Temporal Tracker & Signal Conditioning\n(Adaptive Baselines, Gating, Rates)"]
        Temp --> Buff["10s Rolling Feature Buffer (15 Aggregated Features)"]
        Buff --> RF["Random Forest Classifier (KSS 0 / 5 / 10)"]
        RF --> Norm["Fatigue Score Normalization (0-100 Scale)"]
    end

    subgraph Transport["Real-Time Communication Layer (server.js)"]
        Norm --> WSPub["WebSocket Client\n(?role=publisher)"]
        Cap -. JPEG Frames .-> FramePub["Camera Frame Transport\n(?role=frame-publisher)"]
        WSPub -->|JSON Telemetry| WSServer["Node.js WebSocket Server (/ws)"]
        FramePub -->|Binary Stream| WSServer
        WSServer -->|Broadcast JSON| WSSub["Browser Subscriber\n(?role=subscriber)"]
        WSServer -->|Internal POST /api/telemetry| APITelem["Next.js Telemetry API Route"]
    end

    subgraph Backend["Core Application & Storage Layer (Next.js)"]
        APITelem --> RiskEng["Risk Engine (lib/risk-engine.ts)\n- Classification: LOW / MODERATE / HIGH / CRITICAL\n- Deduplication & Queue Concurrency Control"]
        RiskEng --> Prisma["Prisma ORM Client"]
        Prisma --> DB[("PostgreSQL Database\n- users\n- pilots\n- flights\n- monitoring_sessions\n- fatigue_measurements\n- risk_history\n- recommendations")]
        
        RiskEng -->|High/Critical Risk Detected\n(5-Min Cooldown)| GemSvc["Gemini Advisory Engine (lib/gemini.ts)"]
        GemSvc -->|Google GenAI API| LLM["Google Gemini 3.8 Flash"]
        LLM -->|Operational Advisory| GemSvc
        GemSvc --> Prisma
    end

    subgraph Frontend["Cockpit & Operations Dashboard (React 19 / Next.js)"]
        WSSub --> LiveProv["LiveMonitoringProvider (React Context)"]
        LiveProv --> Dial["Fatigue Score Dial & State Badge"]
        LiveProv --> SignalGrid["Physiological Metrics Grid\n(Blink Rate, Yawns, Closure, Pose)"]
        LiveProv --> Chart["Dynamic Trend Chart (SVG Time Series)"]
        APITelem -. Poll Recommendations .-> RecPanel["AI Recommendations Panel"]
        AuthUI["Login & Session Controls"] --> AuthAPI["NextAuth (/api/auth) & Session APIs"]
        AuthAPI --> ProcMgr["Worker Manager (lib/worker-manager.ts)"]
        ProcMgr -->|child_process.spawn| Sensing
    end
```

---

## 5. Technology Stack

| Layer | Technology | Version / Specification | Role in System |
|---|---|---|---|
| **Vision Framework** | OpenCV (`opencv-contrib-python`) | `5.0.0.93` | Video capture, frame transforms, perspective-n-point solver, JPEG frame encoding |
| **Landmark Detection** | Google MediaPipe | `1.0.1` (`face_landmarker.task`) | 478 3D dense facial landmarks extracted via float16 vision task |
| **Machine Learning** | Scikit-learn & Joblib | `1.6.1` | SimpleImputer + RandomForestClassifier pipeline for KSS inference |
| **Data Processing** | NumPy & Pandas | `2.4.6` / `2.3.0` | Matrix transformations, geometry calculations, dataset aggregation |
| **Python Runtime** | Python | `3.11.x` | Isolated virtual environment worker (`python-cv/.venv`) |
| **App Framework** | Next.js (App Router) | `16.3.8` | Server components, API routes, layout orchestration |
| **UI Library** | React | `19.2.8` | Component rendering, hooks, live context state management |
| **Styling** | Tailwind CSS & PostCSS | `v4` | Modern cockpit interface design, responsive layouts, data grids |
| **Icons & Primitives** | Lucide React, Radix UI | Latest | Accessible UI components, indicators, and telemetry dials |
| **Real-Time Transport**| `ws` (Node.js) & Native WebSocket | `8.22.0` | Bidirectional low-latency telemetry relay and binary frame streaming |
| **Database & ORM** | PostgreSQL & Prisma ORM | `7.10.0` (Client & pg adapter) | Relational persistence, time-series measurements, session tracking |
| **Authentication** | Auth.js / NextAuth | `4.24.15` (Credentials Provider) | JWT-based session security, bcrypt password hashing |
| **Generative AI** | Google GenAI SDK (`@google/genai`) | `2.28.0` (`gemini-3.8-flash`) | Contextual operational recommendations during high-risk events |

---

## 6. Major System Components

### 1. Python Computer Vision Worker (`python-cv`)
- **`camera/capture.py`:** Manages physical device video streaming, handling resolution, buffer flushing, and FPS tracking.
- **`detection/face_landmarker.py`:** Encapsulates MediaPipe Tasks API. Downloads `face_landmarker.task` on initial launch and outputs framework-agnostic 3D coordinates.
- **`features/eye.py` & `mouth.py`:** Calculates 6-point Eye Aspect Ratio (EAR) per eye and 4-point Mouth Aspect Ratio (MAR).
- **`features/head_pose.py`:** Solves the 2D-to-3D Perspective-n-Point (PnP) problem against a canonical head model to extract continuous pitch, yaw, and roll angles.
- **`temporal/tracker.py`:** Implements dual-hysteresis eyelid state tracking, personal dynamic EAR baselines, debounced yawn counting, and head-jump filtering.
- **`prediction/model.py` & `buffer.py`:** Aggregates a rolling 10-second FIFO buffer into 15 statistical features and executes Random Forest inference.
- **`transport/ws.py`:** Dispatches structured JSON telemetry and JPEG binary frame bytes to `server.js` via WebSocket.

### 2. Node.js WebSocket & Telemetry Relay Server (`server.js`)
- Runs an HTTP server multiplexing Next.js requests and WebSocket upgrades on port 3000.
- Handles role-based WebSocket connections (`publisher`, `subscriber`, `frame-publisher`, `frame-subscriber`).
- Forwards incoming publisher telemetry to connected browser clients immediately and offloads asynchronous persistence to Next.js via internal HTTP POST.

### 3. Application Backend (`src/app/api` & `src/lib`)
- **`worker-manager.ts`:** Programmatically starts and stops the Python child process, linking its lifecycle to the active flight session ID.
- **`risk-engine.ts`:** Processes telemetry payloads sequentially using a Promise queue, stores records in Prisma, and classifies risk.
- **`gemini.ts`:** Communicates with the Google GenAI SDK to generate concise operational recommendations when fatigue crosses safe thresholds.
- **`auth-service.ts` & `auth.ts`:** Manages user authentication, password verification using bcrypt, and role authorization.

### 4. Interactive Cockpit Dashboard (`src/app/(app)`)
- **Dashboard Overview (`/dashboard`):** High-level summary of active sessions, fleet risk statistics, and monitoring session initiation controls.
- **Live Monitoring Console (`/monitoring`):** Real-time monitoring room featuring fatigue score dials, physiological metrics, dynamic SVG trend charts, and AI recommendations.
- **Session History (`/history`):** Complete historical logs of past flight legs with average fatigue scores, durations, and peak risk levels.
- **Reports (`/reports`):** Operational archive of flight summaries and safety review documents.

---

## 7. End-to-End Data Flow

```
[ Webcam Device ]
       │  (30 FPS RGB video stream)
       ▼
[ OpenCV VideoCapture ]
       │  (OpenCV BGR → RGB conversion)
       ▼
[ MediaPipe Face Landmarker ]
       │  (478 dense 3D facial coordinates)
       ▼
[ Geometric Feature Extraction ]
       │  ├── Left/Right EAR
       │  ├── MAR
       │  └── solvePnP (Pitch, Yaw, Roll)
       ▼
[ Temporal Tracker & Signal Conditioning ]
       │  ├── Dynamic EAR baselines (10s rolling median)
       │  ├── Dual-hysteresis state machine (0.75 / 0.85 drops)
       │  ├── Pose jump invalidation (>15° motion rejects false blinks)
       │  ├── Yawn debouncing (min 2.0s duration, 1.0s cooldown)
       │  └── Rolling window rates (blinks/min, yawns/min)
       ▼
[ Prediction Buffer (10s Rolling Window) ]
       │  (Aggregates 15 statistical metrics: mean, min, max, std, median)
       ▼
[ Scikit-Learn Random Forest Pipeline ]
       │  ├── Missing value median imputation
       │  └── Random Forest inference → KSS label (0, 5, 10) & probabilities
       ▼
[ Python WebSocket Transport ]
       │  (Dispatches JSON payload throttled at 1 Hz)
       ▼
[ Node.js WebSocket Server (server.js:3000/ws) ]
       ├── Broadcasts directly to browser subscribers (0 ms transport delay)
       └── Internal POST to http://localhost:3000/api/telemetry
              ▼
       [ Next.js Telemetry API Route ]
              │  (Validates session token and active session status)
              ▼
       [ Risk Engine (lib/risk-engine.ts) ]
              ├── Inserts record into fatigue_measurements table
              ├── Classifies Risk Tier (LOW / MODERATE / HIGH / CRITICAL)
              ├── Updates risk_history table on tier change
              └── Triggers Gemini Advisory Engine (if HIGH/CRITICAL & off cooldown)
                     ▼
              [ Google Gemini Flash 3.8 ]
                     │  (Generates short operational recommendation)
                     ▼
              [ PostgreSQL recommendations Table ]
```

---

## 8. Computer Vision Pipeline

```
+-----------------------------------------------------------------------------+
|                           COMPUTER VISION PIPELINE                          |
+-----------------------------------------------------------------------------+
   Raw Video Frame (640x480 @ 30 FPS)
         │
         ▼
   [MediaPipe Face Landmarker] ──> 478 3D Coordinates
         │
         ├──> Left Eye [362, 385, 387, 263, 373, 380] ─┐
         │                                              ├──> EAR (Eye Aspect Ratio)
         ├──> Right Eye [33, 160, 158, 133, 153, 144]  ─┘
         │
         ├──> Mouth Landmarks [13, 14, 61, 291] ───────────> MAR (Mouth Aspect Ratio)
         │
         └──> 6 Key Face Points [1, 152, 33, 263, 61, 291] ─> solvePnP ──> Pitch, Yaw, Roll
```

### 8.1 Video Ingestion & OpenCV Processing
Frames are acquired using OpenCV's `cv2.VideoCapture` at 30 FPS. Frames are processed in memory and scaled for preview transport over WebSocket to avoid excessive UI render overhead.

### 8.2 MediaPipe Face Landmarker
The system integrates Google MediaPipe Tasks API (`vision.FaceLandmarker`) running in `IMAGE` mode. If `face_landmarker.task` is not detected in `python-cv/models/`, the module downloads the model asset from Google's model repository. The detector extracts 478 normalized Cartesian coordinates $(x, y, z)$ per frame.

### 8.3 Geometric Feature Extraction (EAR, MAR, Head Pose)
The system calculates three core geometric indicators:

1. **Eye Aspect Ratio (EAR):**
   Computed for both left and right eyes using standard 6-point anatomical configurations:
   $$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \cdot \|p_1 - p_4\|}$$
   - Left eye indices: `[362, 385, 387, 263, 373, 380]`
   - Right eye indices: `[33, 160, 158, 133, 153, 144]`

2. **Mouth Aspect Ratio (MAR):**
   Measures vertical mouth opening relative to outer mouth width:
   $$\text{MAR} = \frac{\|p_{13} - p_{14}\|}{\|p_{61} - p_{291}\|}$$

3. **3D Head Pose Estimation:**
   Uses `cv2.solvePnP` with an iterative Levenberg-Marquardt solver, matching 6 2D image coordinates against a generic 3D anthropological head model:
   - Nose tip: `1`
   - Chin: `152`
   - Eye corners: `33` (right), `263` (left)
   - Mouth corners: `61` (right), `291` (left)
   Euler angles (pitch, yaw, roll in degrees) are extracted trigonometrically from the resulting rotation matrix via `cv2.Rodrigues`.

### 8.4 Temporal Feature Tracking & Signal Conditioning
Raw instantaneous geometry is highly susceptible to head motion, individual morphology, and sensor noise. The `TemporalTracker` applies several signal-conditioning techniques:
- **Dynamic Baseline Adaptation:** Maintains a 10-second rolling history of open-eye EAR samples. The baseline is computed using the low-median of open-eye values, adjusting dynamically to individual eye shapes.
- **Dual-Hysteresis State Machine:** Eyelid closure triggers when EAR falls below $0.75 \times \text{baseline}$. Re-opening requires EAR to climb back above $0.85 \times \text{baseline}$, preventing rapid oscillation around a single threshold.
- **Pose-Jump Blink Validation:** If head rotation during closure exceeds $15^\circ$, the candidate blink is discarded to prevent false positives caused by the pilot glancing down at cockpit instruments.
- **Duration Gating:** Genuine blinks are constrained between $0.05\text{ s}$ and $0.6\text{ s}$. Eyelid closures exceeding $3.0\text{ s}$ flag a prolonged closure (microsleep indicator).
- **Debounced Yawn Detection:** Yawning requires $\text{MAR} > 0.35$ sustained for at least $2.0\text{ s}$ with a mandatory $1.0\text{ s}$ cooldown, ignoring brief conversational mouth movements.

---

## 9. Machine Learning Pipeline

```
+-----------------------------------------------------------------------------+
|                          MACHINE LEARNING PIPELINE                          |
+-----------------------------------------------------------------------------+
   Raw Frame Metrics (EAR, MAR, Pitch, Yaw, Roll, Blinks, Yawns)
         │
         ▼
   [Prediction Buffer] (10-Second FIFO Rolling Window)
         │
         ▼
   15 Aggregated Statistical Features:
   ├── ear_mean, ear_min
   ├── mar_mean, mar_max
   ├── blink_rate_mean, blink_rate_max
   ├── yawn_rate_mean, yawn_rate_max
   ├── closure_duration_max
   └── pitch_median, pitch_std, yaw_median, yaw_std, roll_median, roll_std
         │
         ▼
   [SimpleImputer] (Median strategy)
         │
         ▼
   [RandomForestClassifier] (100 estimators, random_state=42)
         │
         ▼
   Predicted Karolinska Sleepiness Scale (KSS):
   ├── KSS 0  -> "Alert"
   ├── KSS 5  -> "Low Vigilant"
   └── KSS 10 -> "Drowsy"
         │
         ▼
   Normalized Score = (KSS / 10.0) * 100.0  --> [0 - 100 Scale]
```

### 9.1 Dataset Preparation (UTA-RLDD)
The model was trained and evaluated using the **UTA-RLDD (University of Texas at Arlington Real-Life Drowsiness Dataset)**:
- Consists of multi-stage video recordings of subjects under controlled vigilance states: Alert (KSS 0), Low Vigilance (KSS 5), and Drowsy (KSS 10).
- Windows are extracted over 10-second rolling segments.
- Combined extracted dataset: **743 total validated windows** across subjects 1, 2, 3, and 5 (Subject 4 was excluded due to incomplete source video segments).

### 9.2 Feature Vector Aggregation
Every second, the 10-second rolling buffer aggregates 15 engineered statistical features:

| Feature Name | Type | Description |
|---|---|---|
| `ear_mean` | Float | Mean Eye Aspect Ratio across the 10-second window |
| `ear_min` | Float | Minimum observed Eye Aspect Ratio (maximum eyelid closure) |
| `mar_mean` | Float | Mean Mouth Aspect Ratio |
| `mar_max` | Float | Peak mouth opening extension |
| `blink_rate_mean` | Float | Rolling average blink frequency (per minute) |
| `blink_rate_max` | Float | Maximum instantaneous blink frequency |
| `yawn_rate_mean` | Float | Average yawn frequency (per minute) |
| `yawn_rate_max` | Float | Maximum yawn frequency |
| `closure_duration_max` | Float | Longest single continuous eye closure duration (seconds) |
| `pitch_median`, `pitch_std` | Float | Central tendency and variation in vertical head tilt |
| `yaw_median`, `yaw_std` | Float | Central tendency and variation in horizontal head turn |
| `roll_median`, `roll_std` | Float | Central tendency and variation in lateral head roll |

### 9.3 Random Forest Classifier Pipeline
The inference model is implemented as a Scikit-learn `Pipeline`:
1. **Imputation:** `SimpleImputer(strategy='median')` resolves any temporary sensor dropouts.
2. **Classification:** `RandomForestClassifier(n_estimators=100, random_state=42)` generates class probability distributions across the 3 KSS categories.
3. **Model Persistence:** Serialized using `joblib` (`fatigue_final.joblib`). If no pre-trained weights are located on disk, the worker automatically runs in safe baseline stub mode to allow UI testing.

### 9.4 Evaluation Methodology & Subject-Independent Validation
Evaluating fatigue detection requires testing on **unseen subjects** rather than random train-test splits. Random splitting causes data leakage because consecutive 10-second windows from the same subject share facial structure and lighting.

The project implemented **Leave-One-Subject-Out Cross-Validation (LOSO-CV)** using Scikit-learn's `LeaveOneGroupOut`. In each fold, all windows from one subject are held out exclusively for testing, while the model is trained entirely on the remaining subjects.

---

## 10. Risk Assessment and Scoring

The system separates raw machine learning inference from operational risk assessment:

1. **Fatigue Score Normalization:**
   The discrete KSS class prediction is scaled to an intuitive 0–100 integer range:
   $$\text{FatigueScore} = \text{round}\left(\frac{\text{KSS}}{10.0} \times 100, 1\right)$$
   - KSS 0 $\rightarrow$ Fatigue Score `0.0` ("Alert")
   - KSS 5 $\rightarrow$ Fatigue Score `50.0` ("Low Vigilance")
   - KSS 10 $\rightarrow$ Fatigue Score `100.0` ("Drowsy")

2. **Deterministic Risk Classification:**
   The `classifyRisk` engine maps fatigue score and raw KSS into four operational tiers:

   | Risk Level | Threshold Criteria | Cockpit Operational Meaning |
   |---|---|---|
   | **`LOW`** | Fatigue Score $\le 40$ and $\text{KSS} < 5$ | Normal operations; pilot alert and responsive. |
   | **`MODERATE`** | Fatigue Score $> 40$ or $\text{KSS} \ge 5$ | Early signs of reduced vigilance; monitor closely. |
   | **`HIGH`** | Fatigue Score $> 65$ or $\text{KSS} \ge 7$ | Elevated fatigue; recommend in-seat rest protocol or task rotation. |
   | **`CRITICAL`** | Fatigue Score $> 80$ or $\text{KSS} \ge 8$ | Impending microsleep or severe drowsiness; alert crew immediately. |

3. **Concurrency Control & Cooldowns:**
   - Sequential Promise chaining in `risk-engine.ts` prevents race conditions when writing time-series records to PostgreSQL.
   - When risk transitions to `HIGH` or `CRITICAL`, a 5-minute cooldown (`RECOMMENDATION_COOLDOWN_MS = 300,000`) prevents repeated calls to the Gemini API on consecutive telemetry frames.

---

## 11. Real-Time WebSocket Communication

The application runs a unified HTTP and WebSocket server on port 3000 (`server.js`). WebSocket upgrades are routed to `/ws` with role query parameters:

```
[ Python CV Worker ]                      [ server.js:3000 ]                   [ Browser Dashboard ]
        │                                         │                                      │
        │── ws://.../ws?role=publisher ──────────>│                                      │
        │   (Publishes JSON telemetry)            │── ws://.../ws?role=subscriber ──────>│
        │                                         │   (Receives live telemetry JSON)     │
        │── ws://.../ws?role=frame-publisher ────>│                                      │
        │   (Publishes JPEG preview bytes)        │── ws://.../ws?role=frame-subscriber >│
        │                                         │   (Receives binary JPEG stream)      │
```

### Telemetry Payload Schema
Every second, the publisher sends a JSON message conforming to this structure:

```json
{
  "sessionId": "4f9d2c18-9b88-4672-8f12-9c123456789a",
  "sequence": 142,
  "timestamp": "2026-10-12T01:30:00.000Z",
  "fatigueScore": 50.0,
  "eyeClosurePercent": 12.4,
  "blinkRatePerMin": 18.0,
  "yawnCount": 2,
  "headPoseDeviation": 8.5,
  "alertsTriggered": 0,
  "kss": 5,
  "state": "Low Vigilant",
  "generation": 1
}
```

### Pipeline Robustness
- **Sequence & Generation Tracking:** Each publisher assigns an incrementing `sequence` number. On process restarts, `generation` increments, instructing the dashboard to reset sequence tracking and ignore stale or out-of-order packets.
- **Sub-Second Latency:** WebSocket subscribers receive telemetry immediately upon ingestion without waiting for database persistence.
- **Internal API Offloading:** The WebSocket server forwards telemetry to Next.js via internal HTTP POST (`http://localhost:3000/api/telemetry`), secured with an internal bearer token header (`x-telemetry-token`).

---

## 12. Next.js Dashboard

The frontend is built using Next.js 16 App Router, React 19, and Tailwind CSS v4.

```
+-----------------------------------------------------------------------------+
|                      LIVE MONITORING COCKPIT CONSOLE                        |
+-----------------------------------------------------------------------------+
| Pilot: Capt. Morrison  | Flight: AA-2847 | Elapsed: 1h 42m | [STOP MONITOR] |
+---------------------------------------+-------------------------------------+
|         FATIGUE SCORE DIAL            |         SIGNAL METRICS GRID         |
|                [ 50 ]                 |  - Eye Closure: 12.4%               |
|            MODERATE RISK              |  - Blink Rate:  18 /min             |
|         State: Low Vigilant           |  - Yawns:       2 total             |
|                                       |  - Pose Dev:    8.5 deg             |
+---------------------------------------+-------------------------------------+
|         FATIGUE TREND CHART           |       AI ADVISORY & ALERTS          |
|      (SVG 50-Sample Time Series)      |  - 14:05 [HIGH] Recommend crew rest |
|                                       |  - Status: Gemini Engine Ready      |
+---------------------------------------+-------------------------------------+
```

### Dashboard Features
- **Fatigue Score Panel:** Central circular gauge showing the current fatigue score, colored risk badge (`Low` = Green, `Moderate` = Orange, `High` = Red, `Critical` = Crimson), and KSS classification state.
- **Signal Metrics Panel:** Live grid tracking eye closure percentage, blink rate per minute, cumulative yawn count, head pose deviation, and real-time WebSocket connection status (`Connected`, `Connecting`, `Disconnected`).
- **Fatigue Trend Chart:** Real-time SVG time-series graph displaying a rolling window of the last 50 telemetry measurements.
- **AI Recommendations Panel:** Live feed of operational advisories generated by Google Gemini, categorized by severity badges.
- **Session Controls:** Modal dialogs for selecting pilot flights, initializing monitoring sessions, and triggering safe worker shutdowns.

---

## 13. API, Authentication, and Session Management

### Authentication Architecture
- **Auth.js / NextAuth v4:** Configured in `src/lib/auth.ts` with JWT session strategy (8-hour token lifetime corresponding to a standard aviation duty shift).
- **Credential Verification (`auth-service.ts`):** Validates email and password credentials against the PostgreSQL `users` table using `bcryptjs` salt hashing.
- **Middleware Protection (`src/middleware.ts`):** Protects all application routes (`/dashboard`, `/monitoring`, `/history`, `/reports`), redirecting unauthenticated requests to `/login`.

### Key REST API Endpoints

| Method | Endpoint | Authorization | Description |
|---|---|---|---|
| `POST` | `/api/auth/[...nextauth]` | Public | NextAuth authentication handler (sign in, token refresh, sign out). |
| `POST` | `/api/sessions/start` | Authenticated Pilot | Validates flight assignment, creates an `ACTIVE` session, and spawns the Python CV worker. |
| `POST` | `/api/sessions/stop` | Authenticated Pilot | Gracefully terminates the running Python worker process and marks session `COMPLETED` or `ABORTED`. |
| `POST` | `/api/telemetry` | Internal Token | Internal ingestion endpoint called by `server.js` to trigger risk assessment and database writes. |
| `GET` | `/api/sessions/[sessionId]/recommendations` | Authenticated Pilot | Returns recent AI recommendations and current Gemini service health status. |

---

## 14. PostgreSQL Database and Prisma ORM

The persistence layer uses PostgreSQL managed through Prisma ORM (`@prisma/client` and `@prisma/adapter-pg`).

### Relational Schema

```mermaid
erDiagram
    User {
        String id PK
        String email UK
        String name
        UserRole role
        String passwordHash
        DateTime createdAt
        DateTime updatedAt
    }

    Pilot {
        String id PK
        String employeeId UK
        String name
        String licenseNumber UK
        String email UK
        DateTime createdAt
    }

    Flight {
        String id PK
        String flightCode UK
        String origin
        String destination
        DateTime scheduledAt
        String pilotId FK
    }

    MonitoringSession {
        String id PK
        SessionStatus status
        DateTime startedAt
        DateTime endedAt
        Int alertCount
        String pilotId FK
        String flightId FK
    }

    FatigueMeasurement {
        String id PK
        DateTime capturedAt
        Float fatigueScore
        Float eyeClosurePercent
        Float blinkRatePerMin
        Int yawnCount
        Float headPoseYaw
        Float headPosePitch
        String sessionId FK
    }

    RiskHistory {
        String id PK
        RiskLevel riskLevel
        Float fatigueScore
        DateTime triggeredAt
        DateTime resolvedAt
        String sessionId FK
    }

    Recommendation {
        String id PK
        RecommendationType type
        RiskLevel severity
        String message
        DateTime issuedAt
        DateTime acknowledgedAt
        String sessionId FK
    }

    Pilot ||--o{ Flight : assigns
    Pilot ||--o{ MonitoringSession : participates
    Flight ||--o{ MonitoringSession : operates
    MonitoringSession ||--o{ FatigueMeasurement : records
    MonitoringSession ||--o{ RiskHistory : transitions
    MonitoringSession ||--o{ Recommendation : generates
```

---

## 15. Gemini AI Recommendation Integration

The system integrates Google Gemini (`gemini-3.8-flash`) via the `@google/genai` SDK to provide contextual decision support:

1. **Trigger Condition:**
   When the risk engine detects a transition into `HIGH` or `CRITICAL` risk and the 5-minute session cooldown has elapsed, it builds an operational prompt:
   ```text
   You are an Aviation Fatigue Risk Engine.
   Pilot metrics: Fatigue Score 70.0/100, KSS: 7, Blink Rate: 8.5/min.
   Current assessed risk level: HIGH.
   Based on this, what is your recommendation? Reply only with short, actionable text.
   ```

2. **Actionable Outputs:**
   The model returns concise, operations-compliant guidance (e.g., *"Recommend in-seat rest protocol. Transfer non-critical flight tasks to first officer."*).

3. **Classification & Persistence:**
   The recommendation is mapped to an operational type (`ALERT_CREW`, `REST_BREAK`, `MONITOR_CLOSELY`, `CREW_CHANGE`, or `NOTIFY_GROUND`) and stored in the database.

4. **Graceful Degradation:**
   If `GEMINI_API_KEY` is not configured, the system logs `missing-key` status and continues monitoring without disruption. Telemetry streaming, risk scoring, and database persistence operate normally.

---

## 16. Security and Privacy Considerations

1. **Biometric Privacy & No Frame Storage:**
   - Raw camera video frames are processed entirely in memory by the local Python worker.
   - Video frames are never written to disk, stored in the database, or transmitted to cloud services.
   - Only non-invertible numerical telemetry (EAR, MAR, blink counts, head angles) is retained.

2. **Credential & Secret Protection:**
   - User passwords are encrypted with `bcryptjs`.
   - Database connection strings, `NEXTAUTH_SECRET`, and `GEMINI_API_KEY` are isolated within `.env` configuration files and excluded from version control (`.gitignore`).

3. **API Authorization & Least Privilege:**
   - The `/api/telemetry` ingestion endpoint requires the secret `x-telemetry-token` matching `NEXTAUTH_SECRET`.
   - Pilot session routes enforce pilot-ownership validation to ensure pilots cannot view or modify sessions belonging to others.

---

## 17. Model Evaluation Results

### Cross-Validation Results (UTA-RLDD Dataset)
The Random Forest classifier was evaluated across 743 10-second windows extracted from the UTA-RLDD dataset using Leave-One-Subject-Out Cross-Validation (LOSO-CV).

| Metric | Fold 1 (Subj 1) | Fold 2 (Subj 2) | Fold 3 (Subj 3) | Fold 4 (Subj 5) | **Aggregate (Overall)** |
|---|---|---|---|---|---|
| **Test Windows** | 182 | 183 | 194 | 184 | **743 Total** |
| **Accuracy** | 36.81% | 14.75% | 18.04% | 29.89% | **24.76% (approx. 21.4% – 24.8%)** |
| **Macro Precision**| 0.3699 | 0.0751 | 0.1783 | 0.2184 | **0.2086** |
| **Macro Recall** | 0.3664 | 0.1475 | 0.1845 | 0.2987 | **0.2453** |
| **Macro F1 Score** | 0.2824 | 0.0929 | 0.1483 | 0.2447 | **0.2113 (baseline ~0.1725)** |

### Per-Class Performance Breakdown

| Class | KSS Level | State Label | Precision | Recall | F1 Score |
|---|---|---|---|---|---|
| **Class 0** | KSS 0 | Alert | 0.2797 | 0.4173 | 0.3349 |
| **Class 1** | KSS 5 | Low Vigilant | 0.1154 | **0.0246 (near 0%)** | 0.0405 |
| **Class 2** | KSS 10 | Drowsy | 0.2308 | 0.2939 | 0.2585 |

### Aggregate Confusion Matrix
```
Predicted ──>    [ Alert (0) ]   [ Low Vigilant (5) ]   [ Drowsy (10) ]
Actual KSS 0:         106                 14                  134
Actual KSS 5:         132                  6                  106
Actual KSS 10:        141                 32                   72
```

### Analysis of Limitations
- **Poor Subject Generalization:** Across unseen subjects, overall classification accuracy hovers around 21.4% to 24.8%, which is below random chance (33.3% on 3-class balanced data). This demonstrates that static morphological features do not generalize easily across individuals.
- **Middle-Class (KSS 5) Collapse:** Recall for the intermediate KSS 5 class drops to near 0% (2.46%). In human subjects, subtle low-vigilance states produce mild, variable physiological signals that tabular models frequently misclassify as either fully alert or drowsy.
- **Subject Morphology Variability:** Differences in resting eye aperture, facial geometry, head movement tendencies, and room lighting across subjects create significant baseline shifts.

> **Academic Honesty Statement:** These empirical results demonstrate that while the computer vision tracking pipeline and real-time architecture function reliably, the tabular Random Forest model is an experimental academic prototype and is **not production-ready or certified for flight operations**.

---

## 18. Limitations and Future Improvements

### Current Limitations
1. **Subject Invariance:** The classifier struggles to separate alertness levels when applied to pilots whose baseline facial features were not part of the training set.
2. **Single Camera Perspective:** Monocular RGB webcams are sensitive to extreme lighting shifts, direct cockpit glare, and nighttime cockpits lacking infrared illumination.
3. **Loss of Facial Visibility:** If the pilot turns their head completely away from the instrument panel or occludes their face with a hand, tracking ceases.

### Future Improvements
1. **Infrared & Multi-Camera Cockpit Arrays:** Incorporate near-infrared (NIR) sensors to enable reliable tracking during night flights and under varying cockpit illumination.
2. **Temporal Deep Learning Architectures:** Replace static window aggregation with recurrent models (LSTM, GRU) or Temporal Convolutional Networks (TCN) trained on raw landmark sequences to capture continuous micro-dynamics.
3. **Personalized In-Flight Calibration:** Implement a 2-minute pre-flight calibration routine during pre-flight checks to establish individualized baseline EAR, blink frequency, and head posture profiles.
4. **Multimodal Biometric Sensor Fusion:** Combine optical vision tracking with physiological sensors such as heart-rate variability (HRV) from cockpit seat sensors and flight-control input variability (control wheel steering jitter).

---

## 19. Installation and Environment Setup

### Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux
- **Node.js:** `v20.x` or later
- **Python:** `v3.11.x` (Python 3.11 is required; 3.12+ may have MediaPipe C++ compatibility issues)
- **PostgreSQL Database:** Running locally on port 5432 or accessible via connection URI
- **Webcam:** Connected USB or integrated webcam

### 1. Repository Setup
```bash
git clone https://github.com/prateekkarna03-coder/pilot-fatigue-detection.git
cd pilot-fatigue-system
```

### 2. Node.js Environment & Dependencies
```bash
npm install
```

Configure environment variables:
```bash
cp .env.example .env
```
Edit `.env` with your credentials:
```env
DATABASE_URL="postgresql://postgres:your_password_here@localhost:5432/pilot_fatigue"
NEXTAUTH_SECRET="your-secure-random-32-character-secret"
NEXTAUTH_URL="http://localhost:3000"
GEMINI_API_KEY="your-google-gemini-api-key"
```

Initialize the database schema:
```bash
npx prisma db push
```

### 3. Python CV Worker Setup
```bash
cd python-cv
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install .[test]
cd ..
```

### 4. Running Automated Tests
- **Python CV & Temporal Pipeline Tests:**
  ```bash
  cd python-cv
  pytest
  cd ..
  ```
- **Node.js Code Standards:**
  ```bash
  npm run lint
  ```

---

## 20. How to Demonstrate the Project

Follow these steps to conduct a live end-to-end demonstration:

1. **Start the Application Server:**
   ```bash
   npm run dev
   ```
   This initializes `server.js` on `http://localhost:3000`, running both the Next.js App Router and the WebSocket server (`/ws`).

2. **Access the Console:**
   Open a web browser and navigate to:
   ```
   http://localhost:3000/login
   ```
   Log in using your registered analyst or pilot account credentials.

3. **Start Monitoring Session:**
   - On the `/dashboard` page, click **Start Monitoring**.
   - Select an assigned pilot flight (e.g., flight `AA-2847`).
   - Click **Confirm & Launch**.
   - The backend `worker-manager` will automatically spawn the Python CV worker process bound to the active session.

4. **Observe Real-Time Telemetry:**
   - Navigate to `/monitoring`.
   - The dashboard connects to `ws://localhost:3000/ws?role=subscriber`.
   - Check the live feedback:
     - **Normal Alert State:** Blinking naturally keeps the Fatigue Score low (0–40) with a `LOW` risk badge.
     - **Simulated Eye Closure:** Close your eyes for >2.5 seconds to watch the Eye Closure metric climb and trigger prolonged closure indicators.
     - **Simulated Yawn:** Open your mouth wide for >2.0 seconds to verify the MAR calculation and increment the yawn counter.
     - **Head Pose:** Tilt or turn your head to observe real-time Euler angle adjustments.

5. **Stop Session:**
   - Click **Stop Monitoring** in the top navigation bar.
   - The backend sends a termination signal to the Python worker and updates the session status in PostgreSQL to `COMPLETED`.
   - Review the persisted metrics in `/history`.

---

## 21. Safety Disclaimer

> [!WARNING]
> **ACADEMIC PROTOTYPE NOTICE:**
> This system is designed solely for academic research, education, and concept demonstration as part of a university semester project. It has **not** been certified by the Federal Aviation Administration (FAA), the European Union Aviation Safety Agency (EASA), or any other civil aviation authority.
> 
> It must **never** be used as a primary, secondary, or backup safety system in actual flight operations, flight training aircraft, or safety-critical transportation environments.

---

## 22. System Design Documentation (PDF)

A comprehensive, formal System Design document covering mathematical derivations, circuit schematics, and extended architectural specifications is designated to be stored at:
```
docs/System-Design.pdf
```

> [!NOTE]
> *The formal PDF document must be generated and added separately to the `docs/` directory prior to final submission.*

---

## License

This project is developed for academic evaluation purposes. All source code is available under the standard academic educational license.
