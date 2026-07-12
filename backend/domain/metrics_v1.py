from typing import Any, Dict, Optional, Tuple


def _get_value(source: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = source.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return float(default)


def calculate_k_im(immob: Dict[str, Any]) -> float:
    return _get_value(immob, "K_IM", "loss_coefficient", default=1.0)


def calculate_sensitivity(bre: Dict[str, Any], mem: Dict[str, Any], immob: Dict[str, Any]) -> float:
    sn_bre = _get_value(bre, "SN", "sensitivity", default=0.0)
    sn_mem = _get_value(mem, "SN", "sensitivity", default=0.0)
    return sn_bre * sn_mem * calculate_k_im(immob)


def calculate_response_time(bre: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    tr_bre = _get_value(bre, "TR", "response_time", default=0.0)
    tr_im = _get_value(immob, "TR", "response_time", default=0.0)
    tr_mem = _get_value(mem, "TR", "response_time", default=0.0)
    return tr_bre + tr_im + tr_mem


def calculate_stability(
    analyte: Optional[Dict[str, Any]],
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
) -> float:
    # Legacy behavior: analyte stability is ignored.
    return min(
        _get_value(bre, "ST", "stability", default=0.0),
        _get_value(immob, "ST", "stability", default=0.0),
        _get_value(mem, "ST", "stability", default=0.0),
    )


def calculate_lod(
    bre: Dict[str, Any],
    mem: Dict[str, Any],
    sensitivity: Optional[float] = None,
    i_read: Optional[float] = None,
    snr_mem: Optional[float] = None,
) -> float:
    # Legacy behavior: use the worse (larger) LoD among active layers.
    return max(
        _get_value(bre, "LOD", "lod", default=0.0),
        _get_value(mem, "LOD", "lod", default=0.0),
    )


def calculate_dynamic_range(
    bre: Dict[str, Any],
    mem: Dict[str, Any],
    lod: Optional[float] = None,
    k_m: Optional[float] = None,
    c_max: Optional[float] = None,
) -> float:
    bio_min = _get_value(bre, "DR_Min", "dr_min", default=0.0)
    bio_max = _get_value(bre, "DR_Max", "dr_max", default=float("inf"))
    mem_min = _get_value(mem, "DR_Min", "dr_min", default=0.0)
    mem_max = _get_value(mem, "DR_Max", "dr_max", default=float("inf"))
    return max(0.0, min(bio_max, mem_max) - max(bio_min, mem_min))


def calculate_reproducibility(
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
    cv: Optional[float] = None,
) -> float:
    return min(
        _get_value(bre, "RP", "reproducibility", default=0.0),
        _get_value(immob, "RP", "reproducibility", default=0.0),
        _get_value(mem, "RP", "reproducibility", default=0.0),
    )


def calculate_half_life(bre: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return min(
        _get_value(bre, "HL", "durability", default=0.0),
        _get_value(immob, "HL", "durability", default=0.0),
        _get_value(mem, "HL", "durability", default=0.0),
    )


def normalize_metric(
    value: float,
    min_value: float,
    max_value: float,
    greater_is_better: bool,
) -> float:
    if max_value == min_value:
        return 0.0
    if greater_is_better:
        norm = (value - min_value) / (max_value - min_value)
    else:
        norm = (max_value - value) / (max_value - min_value)
    return max(0.0, min(1.0, norm))


def compute_data_completeness_vector(structure: Dict[str, Any]) -> Tuple[Dict[str, int], float, str]:
    required = {
        "SN_BRE": structure.get("SN_BRE") is not None,
        "SN_MEM": structure.get("SN_MEM") is not None,
        "K_IM": structure.get("K_IM") is not None,
        "TR_BRE": structure.get("TR_BRE") is not None,
        "TR_MEM": structure.get("TR_MEM") is not None,
        "ST_BRE": structure.get("ST_BRE") is not None,
        "ST_IM": structure.get("ST_IM") is not None,
        "ST_MEM": structure.get("ST_MEM") is not None,
        "LOD": structure.get("LOD") is not None,
        "DR": structure.get("DR") is not None,
        "RP": structure.get("RP") is not None,
        "HL": structure.get("HL") is not None,
    }
    vector = {key: int(value) for key, value in required.items()}
    eta = sum(vector.values()) / len(vector) if vector else 1.0
    if eta >= 0.9:
        label = "full"
    elif eta >= 0.6:
        label = "partial"
    else:
        label = "critical"
    return vector, eta, label


def calculate_combination_metrics(
    analyte: Dict[str, Any],
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
) -> Dict[str, float]:
    metrics = {
        "SN_total": calculate_sensitivity(bre, mem, immob),
        "TR_total": calculate_response_time(bre, immob, mem),
        "ST_total": calculate_stability(analyte, bre, immob, mem),
        "LOD_total": calculate_lod(bre, mem),
        "DR_total": calculate_dynamic_range(bre, mem),
        "RP_total": calculate_reproducibility(bre, immob, mem),
        "HL_total": calculate_half_life(bre, immob, mem),
    }
    metrics["PC_total"] = (
        _get_value(bre, "PC", "power_consumption", default=0.0)
        + _get_value(immob, "PC", "power_consumption", default=0.0)
        + _get_value(mem, "PC", "power_consumption", default=0.0)
    )
    return metrics
