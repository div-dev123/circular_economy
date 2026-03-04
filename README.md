# ♻️ CircularConnect — AI-Powered Circular Economy Platform

A full-stack industrial waste exchange platform that connects waste producers with companies that can reuse those materials as raw inputs — closing the loop in India's circular economy. Built with **React 19**, **Flask**, **PyTorch**, and a **5-database polyglot persistence** architecture.

![React](https://img.shields.io/badge/React-19.2-61DAFB?logo=react)
![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask)
![PyTorch](https://img.shields.io/badge/PyTorch-2.10-EE4C2C?logo=pytorch)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-4169E1?logo=postgresql)
![Neo4j](https://img.shields.io/badge/Neo4j-5-008CC1?logo=neo4j)
![MongoDB](https://img.shields.io/badge/MongoDB-5-47A248?logo=mongodb)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)
![Cassandra](https://img.shields.io/badge/Cassandra-4-1287B1?logo=apachecassandra)

---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [AI Matching Algorithm](#ai-matching-algorithm)
- [Database Architecture (5 DBs)](#database-architecture-5-dbs)
- [API Endpoints](#api-endpoints)
- [Frontend Pages](#frontend-pages)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)

---

## Overview

Indian industries generate millions of tonnes of waste annually — metal scrap, organic residues, plastics, e-waste, construction debris, and more. Most of it ends up in landfills even though other industries could use it as raw material.

**CircularConnect** solves this by:
1. **Classifying** waste from images using an EfficientNet-B3 CNN (11 waste categories)
2. **Matching** waste producers with compatible buyer companies using a 6-stage hybrid ML + rule-based pipeline
3. **Connecting** them via real-time chat and a structured deal system
4. **Tracking** environmental impact (CO₂ saved, landfill diverted, energy recovered) across every transaction

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 19 + Vite)               │
│   Login → Classify → Match → Chat → Deal → Dashboard → Deals   │
└────────────────────────────┬────────────────────────────────────┘
                             │  /api proxy (port 5173 → 5002)
┌────────────────────────────▼────────────────────────────────────┐
│                     BACKEND (Flask + PyTorch)                    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ EfficientNet │  │  Matching    │  │  Chat / Deal / Notify  │ │
│  │ B3 Classifier│  │  Engine (6   │  │  System                │ │
│  │ (11 classes) │  │  stages)     │  │                        │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────────┐ ┌───────┐ ┌───────────┐
│Postgr│ │Neo4j │ │ MongoDB  │ │ Redis │ │ Cassandra │
│ SQL  │ │      │ │          │ │       │ │           │
│Users │ │Graph │ │Documents │ │Cache  │ │TimeSeries │
│Deals │ │Paths │ │Activity  │ │Rate   │ │Analytics  │
│Chat  │ │Rels  │ │History   │ │Limit  │ │Audit Logs │
└──────┘ └──────┘ └──────────┘ └───────┘ └───────────┘
 :5433    :7687     :27017      :6379      :9042
```

Every significant user action (classification, match query, message, deal) **fans out to all 5 databases** — each storing the data in the format it's best at.

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 19.2 | UI framework |
| Vite | 8.0 (beta) | Build tool & dev server |
| React Router | 7.13 | Client-side routing |
| Leaflet + React-Leaflet | 1.9 / 5.0 | Interactive map (India) |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Flask | 2.3.3 | REST API server |
| PyTorch | 2.10 | Deep learning framework |
| timm (EfficientNet-B3) | — | Pre-trained CNN for waste classification |
| scikit-learn | — | Cosine similarity, KNN, MinMaxScaler, OneHotEncoder |
| SciPy | — | Hungarian algorithm (linear_sum_assignment) |
| NumPy | 1.24 | Numerical computing |

### Databases (all Dockerised)
| Database | Type | Port | Purpose |
|---|---|---|---|
| **PostgreSQL 13** | Relational | 5433 | Users, auth, deals, chat, notifications |
| **Neo4j 5** | Graph | 7474 / 7687 | Supply chain network, company relationships |
| **MongoDB 5** | Document | 27017 | Classification history, activity feed, waste listings |
| **Redis 7** | Key-Value | 6379 | Caching, rate limiting, online presence, counters |
| **Cassandra 4** | Column-Family | 9042 | Time-series analytics, environmental metrics, audit logs |

---

## Features

### 🔐 Authentication & Profiles
- Email/password registration with **PBKDF2-HMAC-SHA256** hashing
- Protected routes (all pages except login/signup require auth)
- Editable company profiles with Indian city geocoding (30 cities)

### 📸 AI Waste Classification
- Upload a waste image → **EfficientNet-B3** CNN classifies it into one of **11 categories**:
  `Metal, Plastic, Paper/Cardboard, Glass, Organic, Textile, Construction, Hazardous, Industrial Ash, Electronic, Mixed`
- Multi-label sigmoid output with confidence percentages
- Results cached in **Redis** (by image SHA-256 hash, 1h TTL)
- **Rate limited** at 30 classifications/minute per IP
- Each classification is recorded in all 5 databases

### 🤖 AI Company Matching
- 6-stage hybrid pipeline (see [algorithm section](#ai-matching-algorithm) below)
- Rule-based compatibility acts as a **hard gate** — incompatible industries are eliminated before ML scoring
- Interactive animated pipeline visualization during matching
- Results page with expandable score breakdowns per company

### 🗺️ Industry Network Map
- **Leaflet** interactive map of India with all registered companies
- Filter by industry, search by company/city name
- Distance calculation from your company (Haversine)
- Overlapping marker jittering for dense areas
- Map view + list view toggle

### 💬 Real-Time Chat
- 1-on-1 conversations between matched companies
- Unread message counts and conversation list
- **Green online indicator** with Redis heartbeat (30s TTL)
- Automatic notification creation on new messages

### 🤝 Deal System
- Propose deals from chat (waste type, quantity in tonnes, price in ₹)
- Deal lifecycle: `active → completed / cancelled`
- Environmental impact auto-calculated on deal completion (CO₂ saved, landfill diverted)
- Deal events recorded in all 5 databases

### 📊 Dashboard
- Live platform analytics from all 5 databases
- Stat cards: Total Users, Classifications, Deals Done, Environmental Impact
- Refreshes from API (not stale localStorage)

### 📈 Deal Analytics & History
- Comprehensive `/deals` page with:
  - Stat cards (total deals, active, completed, revenue)
  - Partner grid with deal counts
  - Filterable deal table
  - **Cassandra** timeline of deal events
  - **MongoDB** activity feed
  - **Redis** live platform counters
  - Database source badges showing which DB each section pulls from

### 🔔 Notifications
- Auto-triggered on: new message, deal proposed, deal accepted/completed
- Header bell icon with unread count (polling)
- Dropdown with clickable notifications → navigates to relevant page
- Mark as read (individual or all)

### 🇮🇳 India-Focused
- All pricing in ₹ (INR)
- Quantities in tonnes
- 30 Indian cities with geocoding (Mumbai, Delhi, Bangalore, Chennai, etc.)
- Indian industry types (Tata Steel, Reliance Polymers, Hindalco Aluminum, etc.)

---

## AI Matching Algorithm

The matching engine uses a **6-stage pipeline** to find the best companies for a given waste type:

```
 ┌─────────────────────┐
 │  ALL COMPANIES (DB)  │
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 0: Exclude   │  Remove the requesting user
 │  Self               │
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 1: HARD GATE │  Rule-based compatibility filter
 │  🚪 PASS / REJECT   │  Waste → Industry affinity table
 │                     │  If affinity = 0 → ELIMINATED
 └─────────┬───────────┘
           ▼  (only compatible companies remain)
 ┌─────────────────────┐
 │  Stage 2: Cosine    │  One-hot encode industry + waste type
 │  Similarity (35%)   │  + normalised lat/lng + activity score
 │  🧠 ML              │  → cosine similarity
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 3: KNN (20%) │  k-Nearest-Neighbours in feature
 │  🔬 ML              │  space → rank score (1.0 → 0.0)
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 4: Distance  │  Haversine great-circle distance
 │  (45%) 📍           │  Inverted: closer = higher score
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 5: Blend     │  final = 0.35×sim + 0.20×knn
 │  ⚖️ Weighted Sum    │         + 0.45×distance
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  Stage 6: LP Tie-   │  Hungarian algorithm gives +0.02
 │  Breaking ⚙️        │  bonus to globally optimal match
 └─────────┬───────────┘
           ▼
 ┌─────────────────────┐
 │  TOP K RESULTS      │  Sorted by final_score desc
 └─────────────────────┘
```

### Compatibility Table (Stage 1 — Hard Gate)

Maps 11 waste types to compatible industries with affinity scores (0–1):

| Waste Type | Top Compatible Industries (affinity) |
|---|---|
| Metal | Steel (0.95), Aluminum (0.95), Metals & Mining (0.90), Automobile (0.80) |
| Plastic | Plastics (0.95), Rubber (0.85), Manufacturing (0.70), Chemicals (0.65) |
| Organic | Agriculture (0.95), Food Processing (0.85), Renewable Energy (0.70) |
| Glass | Glass (0.95), Ceramics (0.85), Construction (0.60) |
| Paper/Cardboard | Paper & Pulp (0.95), Packaging (0.90), Recycling (0.80) |
| Textile | Textiles (0.95), Fashion (0.85), Recycling (0.70) |
| Electronic | Electronics (0.90), IT Hardware (0.85), Metals & Mining (0.60) |
| Construction | Construction (0.90), Cement (0.85), Manufacturing (0.60) |
| Hazardous | Waste Management (0.90), Chemicals (0.80), Pharmaceuticals (0.60) |
| Industrial Ash | Cement (0.90), Construction (0.85), Agriculture (0.40) |
| Mixed | Recycling (0.85), Waste Management (0.80), Manufacturing (0.50) |

If a company's industry is **not in the table** for the waste type → it's eliminated. No amount of proximity or ML similarity can save an incompatible company.

### Scoring Weights (Stage 5)

| Factor | Weight | Rationale |
|---|---|---|
| **Distance (Haversine)** | 45% | Logistics cost dominates — closer = cheaper transport |
| **ML Cosine Similarity** | 35% | Feature-space compatibility of profiles |
| **KNN Ranking** | 20% | Structural neighbourhood in feature space |

---

## Database Architecture (5 DBs)

### PostgreSQL — Relational Core
The source of truth for structured, transactional data.

| Table | Purpose |
|---|---|
| `users` | Accounts (email, password_hash, salt, company, industry, location, lat/lng) |
| `companies` | Extended company registry (capacity, certifications as JSONB) |
| `waste_types` | Waste type catalog with processing methods |
| `conversations` | Chat conversations (unique user1/user2 pairs) |
| `messages` | Chat messages (with read receipts) |
| `deals` | Deal lifecycle: active → completed / cancelled |
| `notifications` | User notifications (type, title, body, link, is_read) |
| `compliance_standards` | Regulatory standards (JSONB requirements) |

### Neo4j — Graph Database
Models the supply chain network and company relationships.

**Nodes:** `:Company`, `:Waste`, `:Industry`, `:WasteType`, `:Product`

| Relationship | Meaning |
|---|---|
| `MATCHED_WITH` | ML matching result (score, waste_type) |
| `CHATTED_WITH` | Chat connection (waste_context, count) |
| `DEALT_WITH` | Completed deal (waste_type, total_quantity) |
| `SUPPLIED_TO` | Waste → Industry supply link |
| `PRODUCES` | Industry → Product |
| `GENERATES` | Product → Waste (circular loop) |

Key queries: `find_circular_pathways()` traces full Waste → Industry → Product → Waste → Industry loops up to 5 hops.

### MongoDB — Document Store
Flexible document storage for unstructured and semi-structured data.

| Collection | Purpose |
|---|---|
| `classification_history` | Full classification results with all metadata |
| `activity_feed` | Stream of all user actions (match, message, deal events) |
| `user_profiles` | Extended user documents |
| `waste_listings` | Marketplace listings (text search + geospatial indexes) |
| `transactions` | Transaction history documents |
| `user_preferences` | User preference tracking |

Also uses **GridFS** for waste image storage.

### Cassandra — Time-Series & Audit
Optimised for high-write time-series data with time-bucketed partitions.

| Table | Partition Key | Purpose |
|---|---|---|
| `transactions` | transaction_id (UUID) | Transaction records |
| `environmental_impact` | category + date | CO₂ savings, waste diversion by date |
| `audit_logs` | entity_type | Audit trail (clustered by timestamp DESC) |
| `analytics_timeseries` | event_type | All events: classification, match, chat, deal (clustered by timestamp DESC) |

### Redis — Cache & Real-Time
Sub-millisecond reads for caching, rate limiting, and real-time features.

| Key Pattern | TTL | Purpose |
|---|---|---|
| `classify:<sha256>` | 1h | Classification result cache |
| `match:<waste>:<user>` | 5min | Match result cache |
| `ratelimit:classify:<ip>` | 1min | Rate limiting (30 req/min) |
| `user:online:<id>` | 30s | Online presence heartbeat |
| `session:<id>` | 1h | User session data |
| `stats:classifications:total` | — | Classification counter |
| `stats:deals:completed` | — | Deal completion counter |
| `stats:deals:total_value` | — | Cumulative deal value (₹) |

---

## API Endpoints

### Health & Classification
| Method | Route | Description |
|---|---|---|
| GET | `/api/health` | Health check — model status + all 5 DB states |
| POST | `/api/classify` | AI waste classification (image upload) |

### Matching
| Method | Route | Description |
|---|---|---|
| GET | `/api/match-companies` | Hybrid ML + rule-based matching |
| GET | `/api/smart-match` | Scored + ranked matches (for Matches page) |
| GET | `/api/companies/map` | All companies with coordinates for map |

### Authentication
| Method | Route | Description |
|---|---|---|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/logout` | User logout |
| PUT | `/api/auth/profile` | Update user profile |

### Chat & Messaging
| Method | Route | Description |
|---|---|---|
| GET | `/api/chat/conversations` | List conversations (with online status) |
| POST | `/api/chat/start` | Start or resume a conversation |
| GET | `/api/chat/messages/<id>` | Get messages in a conversation |
| POST | `/api/chat/messages/<id>` | Send a message |
| GET | `/api/chat/unread-count` | Total unread message count |

### Deals
| Method | Route | Description |
|---|---|---|
| POST | `/api/deals` | Create a deal proposal |
| GET | `/api/deals/conversation/<id>` | Deals in a conversation |
| PUT | `/api/deals/<id>/accept` | Accept a deal |
| PUT | `/api/deals/<id>/complete` | Complete a deal (calculates impact) |
| PUT | `/api/deals/<id>/cancel` | Cancel a deal |
| GET | `/api/user/deals` | All deals for a user |
| GET | `/api/user/deal-analytics` | Rich analytics from all 5 DBs |

### Notifications
| Method | Route | Description |
|---|---|---|
| GET | `/api/notifications` | Get notifications for a user |
| GET | `/api/notifications/count` | Unread notification count |
| PUT | `/api/notifications/<id>/read` | Mark notification as read |
| PUT | `/api/notifications/read-all` | Mark all as read |

### Analytics & Network
| Method | Route | Description |
|---|---|---|
| GET | `/api/analytics/dashboard` | Platform analytics from all 5 DBs |
| GET | `/api/analytics/activity` | Activity history (MongoDB) |
| GET | `/api/analytics/classifications` | Classification history (MongoDB) |
| GET | `/api/analytics/supply-chain` | Supply chain insights (Neo4j) |
| GET | `/api/analytics/environmental` | Environmental impact report |
| GET | `/api/network/graph` | Company relationship graph (Neo4j) |

---

## Frontend Pages

| Route | Page | Description |
|---|---|---|
| `/login` | Login | Email/password login |
| `/signup` | Signup | Registration with company details |
| `/` | Home | Landing page with platform overview |
| `/about` | About | Platform mission and team |
| `/how-it-works` | How It Works | Step-by-step platform guide |
| `/marketplace` | Marketplace | Interactive India map with all companies |
| `/classify` | Classify | AI waste image classification + animated matching |
| `/matches` | Matches | AI-scored company matches with pipeline visualization |
| `/dashboard` | Dashboard | Live analytics dashboard |
| `/deals` | Deal Analytics | Deal history, charts, all 5 DB sections |
| `/chat` | Chat | Real-time messaging + deal proposals |
| `/profile` | Profile | Editable company profile |
| `/impact` | Impact | Environmental impact tracking |
| `/business` | Business | Business model information |
| `/contact` | Contact | Contact form |

All pages except `/login` and `/signup` are protected by authentication.

---

## Getting Started

### Prerequisites
- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **Docker** & **Docker Compose**

### 1. Start the databases

```bash
cd backend
docker compose up -d
```

Verify all 5 services are running:
```bash
docker compose ps
```

### 2. Install & run the backend

```bash
cd backend
pip install -r requirements.txt
pip install -r database_requirements.txt
python3 app.py
```

The Flask server starts on **http://localhost:5002**.

### 3. Install & run the frontend

```bash
npm install
npm run dev
```

The Vite dev server starts on **http://localhost:5173** with API proxy to port 5002.

### 4. Open in browser

Navigate to `http://localhost:5173`. You'll be redirected to the login page. Create an account to get started.

### 5. Stop everything

```bash
# Stop databases
cd backend && docker compose down

# Stop backend
Ctrl+C (or kill the Flask process)

# Stop frontend
Ctrl+C
```

### Default Credentials
| Service | Username | Password |
|---|---|---|
| Neo4j | `neo4j` | `password` |
| PostgreSQL | `postgres` | `postgres` (port 5433) |
| MongoDB | — | No auth (dev mode) |
| Redis | — | No auth (dev mode) |
| Cassandra | — | No auth (dev mode) |

---

## Project Structure

```
circular_economy/
├── README.md
├── package.json
├── vite.config.js              # Vite config + /api proxy
├── index.html
│
├── src/                        # React frontend
│   ├── main.jsx                # Entry point
│   ├── App.jsx                 # Router + protected routes
│   ├── App.css / index.css     # Global styles
│   ├── components/
│   │   ├── Header.jsx/css      # Nav bar + notification bell
│   │   └── Footer.jsx/css      # Footer
│   └── pages/
│       ├── Home.jsx/css        # Landing page
│       ├── Login.jsx/css       # Login form
│       ├── Signup.jsx/css      # Registration form
│       ├── Classify.jsx/css    # AI classification + matching animation
│       ├── Matches.jsx/css     # AI-scored match results + pipeline viz
│       ├── Marketplace.jsx/css # India map + company list
│       ├── Chat.jsx/css        # Messaging + deals
│       ├── Dashboard.jsx/css   # Analytics dashboard
│       ├── DealHistory.jsx/css # Deal analytics (all 5 DBs)
│       ├── Impact.jsx/css      # Environmental impact
│       ├── About.jsx/css       # About page
│       ├── HowItWorks.jsx/css  # How it works
│       ├── Business.jsx/css    # Business model
│       └── Contact.jsx/css     # Contact form
│
├── backend/
│   ├── app.py                  # Flask API server (all endpoints)
│   ├── matching_engine.py      # 6-stage hybrid ML matching pipeline
│   ├── model.pth               # Trained EfficientNet-B3 weights
│   ├── requirements.txt        # Python ML dependencies
│   ├── database_requirements.txt # DB driver packages
│   ├── docker-compose.yml      # All 5 database services
│   └── database/
│       ├── database_manager.py # Unified 5-DB orchestrator
│       ├── postgresql_manager.py # Relational core
│       ├── neo4j_manager.py    # Graph database
│       ├── mongodb_manager.py  # Document store
│       ├── cassandra_manager.py # Time-series
│       ├── redis_manager.py    # Cache & real-time
│       └── config.py           # Connection configs
│
└── public/                     # Static assets
```

---

## License

This project was built as an academic demonstration of polyglot persistence and AI-driven circular economy concepts.
- **Keep credentials** in `backend/.env` aligned with `backend/docker-compose.yml`

