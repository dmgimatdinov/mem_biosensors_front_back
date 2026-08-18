import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from services.score_normalizer import calculate_score as legacy_calculate_score

DEFAULT_CRITERIA = ["SN", "TR", "ST", "RP", "LoD"]
LOWER_IS_BETTER = {
    "lod", "lod_total", "tr", "tr_total", "pc", "pc_total", "response_time", "power_consumption",
    "dr", "dr_total", "cost", "distance"
}
RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def _normalize_vector(values: List[float]) -> List[float]:
    total = sum(max(v, 1e-12) for v in values)
    if total <= 0:
        return [1.0 / len(values)] * len(values)
    return [float(v) / total for v in values]


def _get_value(structure: Any, criterion: str) -> Optional[float]:
    if structure is None:
        return None

    if isinstance(structure, dict):
        if criterion in structure:
            return float(structure[criterion])
        lowered = criterion.lower()
        for key, value in structure.items():
            if str(key).lower() == lowered:
                return float(value)
        aliases = {
            "sn": "SN",
            "sn_total": "SN",
            "tr": "TR",
            "tr_total": "TR",
            "st": "ST",
            "st_total": "ST",
            "rp": "RP",
            "rp_total": "RP",
            "lod": "LoD",
            "lod_total": "LoD",
            "dr": "DR",
            "dr_total": "DR",
            "pc": "PC",
            "pc_total": "PC",
        }
        alias = aliases.get(lowered)
        if alias in structure:
            return float(structure[alias])
        return None

    for attr_name in (criterion, criterion.lower(), criterion.replace("_", "")):
        if hasattr(structure, attr_name):
            return float(getattr(structure, attr_name))
    return None


def _is_lower_better(criterion: str) -> bool:
    return criterion.lower() in LOWER_IS_BETTER


def _score_from_values(values: List[float], weights: List[float], criteria: List[str]) -> float:
    if not values or not weights:
        return 0.0
    normalized = []
    for idx, value in enumerate(values):
        criterion = criteria[idx]
        if _is_lower_better(criterion):
            normalized.append(1.0 / max(float(value), 1e-9))
        else:
            normalized.append(float(value))
    total_weight = sum(abs(float(w)) for w in weights)
    if total_weight <= 0:
        return 0.0
    scaled = [float(v) * float(w) for v, w in zip(normalized, weights)]
    return sum(scaled) / total_weight


def ahp_calculate_weights(matrix: List[List[float]]) -> List[float]:
    if not matrix or not matrix[0]:
        raise ValueError("Matrix must be non-empty")

    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square")

    if n == 1:
        return [1.0]

    values = []
    for row in matrix:
        values.append([float(v) for v in row])

    # Power iteration for the dominant eigenvector.
    vector = [1.0 / n] * n
    for _ in range(100):
        next_vector = [sum(matrix[i][j] * vector[j] for j in range(n)) for i in range(n)]
        next_vector = _normalize_vector(next_vector)
        if max(abs(next_vector[i] - vector[i]) for i in range(n)) < 1e-8:
            vector = next_vector
            break
        vector = next_vector

    return _normalize_vector(vector)


def ahp_check_consistency(matrix: List[List[float]]) -> Tuple[float, float, bool]:
    weights = ahp_calculate_weights(matrix)
    n = len(matrix)
    if n == 1:
        return 0.0, 0.0, True

    numerator = 0.0
    for i in range(n):
        row_sum = sum(matrix[i][j] * weights[j] for j in range(n))
        numerator += row_sum / weights[i]
    lambda_max = numerator / n
    ci = (lambda_max - n) / (n - 1)
    ri = RI_TABLE.get(n, 1.49)
    cr = 0.0 if ri == 0 else ci / ri
    return ci, cr, cr <= 0.1


def pareto_frontier(structures: List[Dict[str, Any]], criteria: List[str]) -> List[Dict[str, Any]]:
    if not structures:
        return []

    if not criteria:
        return list(structures)

    frontier: List[Dict[str, Any]] = []
    for candidate in structures:
        dominated = False
        for other in structures:
            if other is candidate:
                continue
            if _dominates(other, candidate, criteria):
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    return frontier


def _dominates(left: Dict[str, Any], right: Dict[str, Any], criteria: List[str]) -> bool:
    left_scores = []
    right_scores = []
    for criterion in criteria:
        left_value = _get_value(left, criterion)
        right_value = _get_value(right, criterion)
        if left_value is None or right_value is None:
            left_value = 0.0
            right_value = 0.0
        if _is_lower_better(criterion):
            left_scores.append(-float(left_value))
            right_scores.append(-float(right_value))
        else:
            left_scores.append(float(left_value))
            right_scores.append(float(right_value))

    better_or_equal = all(l >= r for l, r in zip(left_scores, right_scores))
    strictly_better = any(l > r for l, r in zip(left_scores, right_scores))
    return better_or_equal and strictly_better


def topsis_rank(structures: List[Dict[str, Any]], criteria: List[str], weights: List[float]) -> List[Tuple[Dict[str, Any], float]]:
    if not structures:
        return []
    if len(weights) != len(criteria):
        raise ValueError("Weights and criteria must have the same length")

    values = []
    for structure in structures:
        row = []
        for criterion in criteria:
            value = _get_value(structure, criterion)
            row.append(float(value if value is not None else 0.0))
        values.append(row)

    normalized = []
    for idx in range(len(criteria)):
        column = [row[idx] for row in values]
        norm = math.sqrt(sum(v * v for v in column)) or 1.0
        normalized.append([value / norm for value in column])

    weighted = []
    for row_idx, row in enumerate(values):
        weighted_row = [normalized[col_idx][row_idx] * weights[col_idx] for col_idx in range(len(criteria))]
        weighted.append(weighted_row)

    ideal_positive = []
    ideal_negative = []
    for col_idx in range(len(criteria)):
        criterion = criteria[col_idx]
        column = [row[col_idx] for row in weighted]
        if _is_lower_better(criterion):
            ideal_positive.append(min(column))
            ideal_negative.append(max(column))
        else:
            ideal_positive.append(max(column))
            ideal_negative.append(min(column))

    scores = []
    for row_idx, row in enumerate(weighted):
        distance_positive = math.sqrt(sum((row[col_idx] - ideal_positive[col_idx]) ** 2 for col_idx in range(len(criteria))))
        distance_negative = math.sqrt(sum((row[col_idx] - ideal_negative[col_idx]) ** 2 for col_idx in range(len(criteria))))
        denominator = distance_positive + distance_negative
        score = 0.0 if denominator == 0 else distance_negative / denominator
        scores.append((structures[row_idx], score))

    return sorted(scores, key=lambda item: item[1], reverse=True)


def epsilon_constraints_optimize(structures: List[Dict[str, Any]], objective: str, constraints: Optional[Dict[str, Tuple[str, float]]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not structures:
        return []
    constraints = constraints or {}

    filtered = []
    for structure in structures:
        if all(_passes_constraint(structure, criterion, op, value) for criterion, (op, value) in constraints.items()):
            filtered.append(structure)

    filtered = sorted(
        filtered,
        key=lambda item: float(_get_value(item, objective) or 0.0),
        reverse=True,
    )

    if limit is not None:
        return filtered[:limit]
    return filtered


def _passes_constraint(structure: Dict[str, Any], criterion: str, op: str, value: float) -> bool:
    actual = _get_value(structure, criterion)
    if actual is None:
        return False
    actual = float(actual)
    value = float(value)
    if op == "<":
        return actual < value
    if op == "<=":
        return actual <= value
    if op == ">":
        return actual > value
    if op == ">=":
        return actual >= value
    if op == "=":
        return actual == value
    raise ValueError(f"Unsupported operator {op}")


class StabilityAnalysis:
    def run(self, structures: List[Dict[str, Any]], weights: List[float], n_simulations: int = 1000, seed: Optional[int] = None, top_k: int = 10) -> Dict[str, Dict[str, Any]]:
        if not structures:
            return {}
        if seed is not None:
            random.seed(seed)

        criteria = self._infer_criteria(structures, len(weights))
        scores: List[List[float]] = []
        ranks_by_structure: Dict[str, List[int]] = {self._structure_id(structure): [] for structure in structures}
        for _ in range(max(1, int(n_simulations))):
            perturbed_weights = self._perturb_weights(weights)
            scored_structures = []
            for structure in structures:
                score = self._weighted_score(structure, criteria, perturbed_weights)
                scored_structures.append((structure, score))
            ranked = sorted(scored_structures, key=lambda item: item[1], reverse=True)
            for idx, (structure, _) in enumerate(ranked, start=1):
                ranks_by_structure[self._structure_id(structure)].append(idx)

        results = {}
        for structure in structures:
            structure_id = self._structure_id(structure)
            ranks = ranks_by_structure[structure_id]
            mean_rank = sum(ranks) / len(ranks) if ranks else 0.0
            freq_top_k = sum(1 for rank in ranks if rank <= max(1, int(top_k))) / len(ranks) if ranks else 0.0
            if freq_top_k >= 0.8:
                label = "stable"
            elif freq_top_k >= 0.6:
                label = "moderate"
            else:
                label = "unstable"
            results[structure_id] = {
                "rank_distribution": ranks,
                "stability_label": label,
                "mean_rank": mean_rank,
            }
        return results

    def sensitivity_to_uncertainty(self, structures: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        base_scores = []
        for structure in structures:
            base_scores.append((structure, self._weighted_score(structure, self._infer_criteria(structures, 4), [0.25, 0.25, 0.25, 0.25])))

        baseline_ranks = {
            self._structure_id(structure): idx + 1
            for idx, (structure, _) in enumerate(sorted(base_scores, key=lambda item: item[1], reverse=True))
        }

        adjusted = []
        for structure in structures:
            adjusted_structure = self._apply_pessimistic_adjustment(structure)
            adjusted.append((structure, adjusted_structure))

        adjusted_scores = []
        for structure, adjusted_structure in adjusted:
            adjusted_scores.append((structure, self._weighted_score(adjusted_structure, self._infer_criteria(structures, 4), [0.25, 0.25, 0.25, 0.25])))

        adjusted_ranks = {
            self._structure_id(structure): idx + 1
            for idx, (structure, _) in enumerate(sorted(adjusted_scores, key=lambda item: item[1], reverse=True))
        }

        results = {}
        for structure in structures:
            structure_id = self._structure_id(structure)
            baseline_rank = baseline_ranks.get(structure_id, 0)
            adjusted_rank = adjusted_ranks.get(structure_id, 0)
            rank_change = adjusted_rank - baseline_rank
            flags = []
            if rank_change >= 5:
                flags.append("requires_experimental_check")
            results[structure_id] = {
                "rank_change": rank_change,
                "flags": flags,
                "baseline_rank": baseline_ranks.get(structure_id, 0),
                "adjusted_rank": adjusted_ranks.get(structure_id, 0),
            }
        return results

    def _infer_criteria(self, structures: List[Dict[str, Any]], count: int) -> List[str]:
        for criterion in DEFAULT_CRITERIA:
            if any(_get_value(structure, criterion) is not None for structure in structures):
                if count <= 0:
                    return []
                return DEFAULT_CRITERIA[:count]
        return ["SN", "TR", "ST", "RP"][:count]

    def _perturb_weights(self, weights: List[float]) -> List[float]:
        perturbed = []
        for weight in weights:
            delta = random.uniform(-0.2, 0.2)
            perturbed.append(max(0.0, float(weight) * (1.0 + delta)))
        total = sum(perturbed) or 1.0
        return [value / total for value in perturbed]

    def _weighted_score(self, structure: Dict[str, Any], criteria: List[str], weights: List[float]) -> float:
        values = []
        for criterion in criteria:
            value = _get_value(structure, criterion)
            if value is None:
                value = 0.0
            values.append(float(value))
        return _score_from_values(values, weights, criteria)

    def _apply_pessimistic_adjustment(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        adjusted = dict(structure)
        reliability_category = str(adjusted.get("reliability_category", "high")).lower()
        if reliability_category not in {"low", "medium"}:
            return adjusted

        penalty = 0.5 if reliability_category == "low" else 0.75
        for criterion in ["SN", "ST", "RP"]:
            if criterion in adjusted:
                adjusted[criterion] = float(adjusted[criterion]) * penalty
        for criterion in ["TR", "LoD", "LOD"]:
            if criterion in adjusted:
                adjusted[criterion] = float(adjusted[criterion]) * (1.0 + (0.5 if reliability_category == "low" else 0.25))
        return adjusted

    def _structure_id(self, structure: Dict[str, Any]) -> str:
        if isinstance(structure, dict):
            if "id" in structure:
                return str(structure["id"])
            if "combo_id" in structure:
                return str(structure["combo_id"])
            if "Combo_ID" in structure:
                return str(structure["Combo_ID"])
        return str(id(structure))


def calculate_score(structures: Any, method: Optional[str] = None, **kwargs: Any) -> Any:
    method_name = (method or kwargs.get("method") or os.getenv("MCDA_METHOD", "weighted_sum") or "weighted_sum").lower()
    if isinstance(structures, dict):
        structures = [structures]

    if method_name == "weighted_sum":
        if not structures:
            return []
        if len(structures) == 1:
            return legacy_calculate_score(structures[0])
        return [legacy_calculate_score(structure) for structure in structures]

    if method_name == "topsis":
        criteria = kwargs.get("criteria") or ["SN", "TR", "ST", "RP"]
        weights = kwargs.get("weights") or [0.4, 0.2, 0.2, 0.2]
        return topsis_rank(list(structures), criteria, weights)

    if method_name == "epsilon":
        return epsilon_constraints_optimize(list(structures), kwargs.get("objective", "SN"), kwargs.get("constraints"), kwargs.get("limit"))

    if method_name == "pareto":
        return pareto_frontier(list(structures), kwargs.get("criteria") or ["LoD", "ST"])

    if method_name == "ahp":
        matrix = kwargs.get("matrix")
        if matrix is None:
            raise ValueError("AHP requires a matrix")
        weights = ahp_calculate_weights(matrix)
        ci, cr, is_consistent = ahp_check_consistency(matrix)
        return {"weights": weights, "CI": ci, "CR": cr, "is_consistent": is_consistent}

    raise ValueError(f"Unsupported MCDA method: {method_name}")
