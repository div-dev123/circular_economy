"""
Material Matching Engine
========================
Hybrid rule-based + ML recommender system for circular economy waste matching.

Components:
  1. Rule-Based Filter   – compatibility tables score waste→industry affinity
  2. ML Similarity        – vectorise (waste type, industry, lat/lng, activity)
                            and compute cosine similarity between profiles
  3. KNN Clustering       – demand-supply balancing via k-nearest-neighbours
  4. LP Optimisation      – maximise total match score while minimising
                            transport distance (SciPy linear programming)
"""

import math
import logging
from typing import List, Dict, Any, Optional

import numpy as np
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
# 1. RULE-BASED COMPATIBILITY TABLES
# ────────────────────────────────────────────────────────────────────

# Waste-type → buyer-industry affinity (0-1 scale)
COMPATIBILITY = {
    'metal': {
        'Steel': 0.95, 'Aluminum': 0.95, 'Metals & Mining': 0.90,
        'Automobile': 0.80, 'Manufacturing': 0.70, 'Construction': 0.65,
        'Electronics': 0.55, 'IT Hardware': 0.50,
    },
    'plastic': {
        'Plastics': 0.95, 'Rubber': 0.85, 'Manufacturing': 0.70,
        'Chemicals': 0.65, 'Automobile': 0.60, 'Construction': 0.40,
    },
    'paper/cardboard': {
        'Paper & Pulp': 0.95, 'Manufacturing': 0.65,
        'Food Processing': 0.50, 'Textiles': 0.35,
    },
    'glass': {
        'Glass': 0.95, 'Ceramics': 0.85, 'Construction': 0.60,
        'Manufacturing': 0.50,
    },
    'organic': {
        'Agriculture': 0.95, 'Food Processing': 0.85,
        'Renewable Energy': 0.70, 'Chemicals': 0.45,
    },
    'textile': {
        'Textiles': 0.95, 'Leather': 0.75,
        'Manufacturing': 0.55, 'Construction': 0.35,
    },
    'construction': {
        'Construction': 0.95, 'Cement': 0.90, 'Steel': 0.70,
        'Manufacturing': 0.55,
    },
    'hazardous': {
        'Chemicals': 0.85, 'Pharmaceuticals': 0.80,
        'Refinery': 0.75,
    },
    'industrial ash': {
        'Cement': 0.95, 'Construction': 0.80,
        'Renewable Energy': 0.55,
    },
    'electronic': {
        'Electronics': 0.95, 'IT Hardware': 0.90,
        'Metals & Mining': 0.75, 'Manufacturing': 0.60,
    },
    'mixed': {
        'Manufacturing': 0.60, 'Renewable Energy': 0.55,
        'Chemicals': 0.50, 'Construction': 0.45, 'Cement': 0.40,
    },
}

# Flat list of every industry that appears anywhere in the tables
ALL_INDUSTRIES = sorted({
    ind for mapping in COMPATIBILITY.values() for ind in mapping
})

ALL_WASTE_TYPES = sorted(COMPATIBILITY.keys())


def rule_score(waste_type: str, industry: str) -> float:
    """Return the rule-based affinity score (0-1) between a waste type and
    a buyer industry.  Returns a small baseline for unknown pairs."""
    return COMPATIBILITY.get(waste_type.lower(), {}).get(industry, 0.05)


# ────────────────────────────────────────────────────────────────────
# 2. FEATURE VECTORISATION + COSINE SIMILARITY
# ────────────────────────────────────────────────────────────────────

class ProfileVectoriser:
    """Encode user profiles into fixed-length numerical vectors so we can
    compute cosine similarity between a producer (waste source) and every
    potential consumer (buyer company)."""

    def __init__(self):
        # One-hot encoder for industry_type
        self._industry_enc = OneHotEncoder(
            categories=[ALL_INDUSTRIES], sparse_output=False, handle_unknown='ignore'
        )
        self._industry_enc.fit(np.array(ALL_INDUSTRIES).reshape(-1, 1))

        self._scaler = MinMaxScaler()
        self._fitted = False

    # ── public helpers ──────────────────────────────────────────────

    def vectorise_producer(self, waste_type: str, latitude: float, longitude: float,
                           quantity: float = 1.0) -> np.ndarray:
        """Build a 'query' vector for the waste producer."""
        # Waste-type one-hot
        wt_vec = np.zeros(len(ALL_WASTE_TYPES))
        wt_lower = waste_type.lower()
        if wt_lower in ALL_WASTE_TYPES:
            wt_vec[ALL_WASTE_TYPES.index(wt_lower)] = 1.0

        # Location embedding (normalised lat/lng)
        loc = np.array([latitude / 90.0, longitude / 180.0])

        # Quantity (log-scaled, capped)
        qty = np.array([min(math.log1p(quantity), 10.0) / 10.0])

        return np.concatenate([wt_vec, loc, qty])

    def vectorise_consumer(self, company: Dict) -> np.ndarray:
        """Build a feature vector for a potential buyer company."""
        # Industry one-hot
        ind_vec = self._industry_enc.transform(
            np.array([[company.get('industry_type', '')]])
        ).flatten()

        # Location
        lat = company.get('latitude', 0) or 0
        lng = company.get('longitude', 0) or 0
        loc = np.array([lat / 90.0, lng / 180.0])

        # Activity proxy (normalised classifications count)
        activity = min((company.get('classifications_count', 0) or 0) / 100.0, 1.0)
        act = np.array([activity])

        return np.concatenate([ind_vec, loc, act])

    def vectorise_consumers_batch(self, companies: List[Dict]) -> np.ndarray:
        """Batch encode feature vectors for a list of buyer companies."""
        if not companies:
            return np.empty((0, len(ALL_INDUSTRIES) + 3))

        industries = np.array([[c.get('industry_type', '')] for c in companies])
        ind_vecs = self._industry_enc.transform(industries)

        loc_acts = np.array([
            [
                (c.get('latitude', 0) or 0) / 90.0,
                (c.get('longitude', 0) or 0) / 180.0,
                min((c.get('classifications_count', 0) or 0) / 100.0, 1.0)
            ]
            for c in companies
        ])

        return np.hstack([ind_vecs, loc_acts])

    def compute_similarity(self, producer_vec: np.ndarray,
                           consumer_vecs: np.ndarray) -> np.ndarray:
        """Cosine similarity between the producer vector and each consumer."""
        if consumer_vecs.ndim == 1:
            consumer_vecs = consumer_vecs.reshape(1, -1)

        # Pad to same length (producer and consumer may differ)
        max_len = max(producer_vec.shape[0], consumer_vecs.shape[1])
        p = np.zeros(max_len)
        p[:producer_vec.shape[0]] = producer_vec

        c = np.zeros((consumer_vecs.shape[0], max_len))
        c[:, :consumer_vecs.shape[1]] = consumer_vecs

        return cosine_similarity(p.reshape(1, -1), c).flatten()


# ────────────────────────────────────────────────────────────────────
# 3. KNN DEMAND-SUPPLY BALANCING
# ────────────────────────────────────────────────────────────────────

def knn_rank(producer_vec: np.ndarray, consumer_vecs: np.ndarray,
             k: int = 10) -> np.ndarray:
    """Use k-Nearest-Neighbours to rank consumers most similar to the
    producer, returning indices sorted by distance (ascending)."""
    max_len = max(producer_vec.shape[0], consumer_vecs.shape[1])
    p = np.zeros(max_len)
    p[:producer_vec.shape[0]] = producer_vec
    c = np.zeros((consumer_vecs.shape[0], max_len))
    c[:, :consumer_vecs.shape[1]] = consumer_vecs

    k = min(k, c.shape[0])
    nn = NearestNeighbors(n_neighbors=k, metric='cosine')
    nn.fit(c)
    distances, indices = nn.kneighbors(p.reshape(1, -1))
    return indices.flatten()


# ────────────────────────────────────────────────────────────────────
# 4. TRANSPORT DISTANCE (Haversine)
# ────────────────────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ────────────────────────────────────────────────────────────────────
# 5. LINEAR-PROGRAMMING OPTIMISATION
# ────────────────────────────────────────────────────────────────────

def optimise_assignments(score_matrix: np.ndarray) -> List[tuple]:
    """Given an (m × n) matrix of match scores (higher = better),
    solve the assignment problem to maximise total score.

    Returns list of (producer_idx, consumer_idx) pairs.
    Uses the Hungarian algorithm via SciPy (works on cost, so we negate).
    """
    cost = -score_matrix  # convert max→min
    row_ind, col_ind = linear_sum_assignment(cost)
    return list(zip(row_ind.tolist(), col_ind.tolist()))


# ────────────────────────────────────────────────────────────────────
# 6. MAIN MATCHING PIPELINE
# ────────────────────────────────────────────────────────────────────

# Weights for the final blended score
# Rule-based compatibility is a HARD GATE (Stage 1) — not blended.
# Only these three decide the ranking among compatible candidates:
W_SIMILARITY = 0.35
W_KNN = 0.20
W_DISTANCE = 0.45

_vectoriser = ProfileVectoriser()


def find_matches(
    waste_type: str,
    producer_lat: float,
    producer_lng: float,
    companies: List[Dict],
    quantity: float = 1.0,
    top_k: int = 15,
    exclude_user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    End-to-end matching pipeline.

    PIPELINE STAGES
    ===============
    Stage 0  – Exclude self
    Stage 1  – RULE-BASED HARD FILTER: Only companies whose industry has
               non-zero compatibility with the waste type proceed.
               This is the gatekeeper — if waste→raw material doesn't match,
               nothing else matters.
    Stage 2  – ML Cosine Similarity scoring on remaining candidates
    Stage 3  – KNN proximity ranking in feature space
    Stage 4  – Geographic distance scoring (Haversine)
    Stage 5  – Weighted blend of all scores → final ranking
    Stage 6  – LP optimisation hint (tie-breaking via Hungarian assignment)

    Parameters
    ----------
    waste_type : str        – classified waste category (e.g. "metal")
    producer_lat, lng       – location of the waste source
    companies : list[dict]  – all candidate buyer companies from the DB
    quantity : float        – approximate tonnage of waste
    top_k : int             – number of results to return
    exclude_user_id : int   – skip this user (typically the producer themselves)

    Returns
    -------
    list of dicts, each with the company data + scoring breakdown, sorted
    by final_score descending.
    """
    if not companies:
        return []

    # ── Stage 0: Exclude the producer themselves ───────────────────
    candidates = [c for c in companies if c.get('id') != exclude_user_id]
    if not candidates:
        return []

    # ── Stage 1: RULE-BASED HARD FILTER ────────────────────────────
    # This is the gatekeeper. If a company's industry has NO entry in the
    # COMPATIBILITY table for this waste type, they are eliminated.
    # Only industries that can actually USE this waste as raw material pass.
    compatible_industries = set(COMPATIBILITY.get(waste_type.lower(), {}).keys())

    filtered = []
    rule_scores_list = []
    for c in candidates:
        industry = c.get('industry_type', '')
        rs = rule_score(waste_type, industry)
        if industry in compatible_industries:
            filtered.append(c)
            rule_scores_list.append(rs)

    # If nobody matched the compatibility table, return empty
    # (no point showing companies that can't use this waste)
    if not filtered:
        logger.info(f"No compatible industries found for waste type '{waste_type}'")
        return []

    candidates = filtered
    rule_scores = np.array(rule_scores_list)
    logger.info(f"Stage 1 filter: {len(candidates)} companies compatible with '{waste_type}' (from {len(companies) - 1} total)")

    # ── Stage 2: ML Cosine Similarity ──────────────────────────────
    prod_vec = _vectoriser.vectorise_producer(waste_type, producer_lat, producer_lng, quantity)
    cons_vecs = _vectoriser.vectorise_consumers_batch(candidates)

    sim_scores = _vectoriser.compute_similarity(prod_vec, cons_vecs)

    # ── Stage 3: KNN ranking (turned into a 0-1 score) ────────────
    k = min(top_k, len(candidates))
    knn_indices = knn_rank(prod_vec, cons_vecs, k=k)
    knn_scores = np.zeros(len(candidates))
    for rank, idx in enumerate(knn_indices):
        knn_scores[idx] = 1.0 - rank / k  # best neighbour = 1.0

    # ── Stage 4: Distance scoring (Haversine, normalised) ──────────
    distances = np.array([
        haversine_km(producer_lat, producer_lng,
                     c.get('latitude') or 0, c.get('longitude') or 0)
        for c in candidates
    ])
    max_dist = distances.max() if distances.max() > 0 else 1.0
    # Invert: closer → higher score
    distance_scores = 1.0 - (distances / max_dist)

    # ── Stage 5: Weighted blend → final score ──────────────────────
    # Rule-based already served as the hard gate in Stage 1.
    # Ranking is purely: how similar + how close + KNN neighbourhood.
    final_scores = (
        W_SIMILARITY * sim_scores +
        W_KNN * knn_scores +
        W_DISTANCE * distance_scores
    )

    # ── Stage 6: LP tie-breaking (if enough candidates) ────────────
    # Use Hungarian assignment to nudge ties toward globally optimal pairing
    if len(candidates) >= 2:
        try:
            score_matrix = final_scores.reshape(1, -1)
            assignments = optimise_assignments(score_matrix)
            # Give a small bonus to the LP-optimal assignment
            for _, ci in assignments:
                if ci < len(final_scores):
                    final_scores[ci] += 0.02
        except Exception:
            pass  # LP is optional, skip if it fails

    # ── Build result list, sort, return top_k ──────────────────────
    results = []
    for i, company in enumerate(candidates):
        results.append({
            **company,
            'match_score': round(float(final_scores[i]) * 100, 1),
            'rule_score': round(float(rule_scores[i]) * 100, 1),
            'similarity_score': round(float(sim_scores[i]) * 100, 1),
            'knn_score': round(float(knn_scores[i]) * 100, 1),
            'distance_km': round(float(distances[i]), 1),
            'distance_score': round(float(distance_scores[i]) * 100, 1),
            'match_reason': _explain(waste_type, company, rule_scores[i], distances[i]),
        })

    results.sort(key=lambda r: r['match_score'], reverse=True)
    return results[:top_k]


def batch_optimise(
    producers: List[Dict],
    consumers: List[Dict],
) -> List[Dict[str, Any]]:
    """Run LP-based optimal assignment across multiple producer↔consumer pairs.

    Each producer dict needs: waste_type, latitude, longitude
    Each consumer dict is a company row from the DB.

    Returns a list of optimal (producer, consumer, score) assignments.
    """
    if not producers or not consumers:
        return []

    n_prod = len(producers)
    n_cons = len(consumers)

    # Build score matrix  (n_prod × n_cons)
    score_matrix = np.zeros((n_prod, n_cons))
    for i, prod in enumerate(producers):
        wt = prod.get('waste_type', 'mixed')
        plat = prod.get('latitude', 0) or 0
        plng = prod.get('longitude', 0) or 0

        for j, cons in enumerate(consumers):
            rs = rule_score(wt, cons.get('industry_type', ''))
            dist = haversine_km(plat, plng,
                                cons.get('latitude') or 0,
                                cons.get('longitude') or 0)
            # Combine rule score and distance into one metric
            dist_penalty = max(0, 1.0 - dist / 3000.0)  # India max ~3000 km
            score_matrix[i, j] = 0.6 * rs + 0.4 * dist_penalty

    assignments = optimise_assignments(score_matrix)

    results = []
    for pi, ci in assignments:
        results.append({
            'producer': producers[pi],
            'consumer': consumers[ci],
            'score': round(float(score_matrix[pi, ci]) * 100, 1),
        })
    results.sort(key=lambda r: r['score'], reverse=True)
    return results


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _explain(waste_type: str, company: Dict, rs: float, dist: float) -> str:
    """Human-readable one-liner explaining why this match was recommended."""
    industry = company.get('industry_type', 'Unknown')
    wt = waste_type.capitalize()

    if rs >= 0.85:
        reason = f"Excellent compatibility — {industry} industry is a primary consumer of {wt} waste"
    elif rs >= 0.60:
        reason = f"Good fit — {industry} commonly processes {wt} materials"
    elif rs >= 0.35:
        reason = f"Moderate match — {industry} can utilise some {wt} by-products"
    else:
        reason = f"Potential match — {industry} may find use for {wt} derivatives"

    if dist < 100:
        reason += " • Very close proximity"
    elif dist < 500:
        reason += f" • {dist:.0f} km away (regional)"
    else:
        reason += f" • {dist:.0f} km away"

    return reason
