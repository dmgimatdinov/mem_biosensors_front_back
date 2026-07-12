import math
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


def calculate_k_im(immob: Dict[str, Any], d_im: Optional[float] = None, d_eff: Optional[float] = None) -> float:
    if immob.get("K_IM") is not None or immob.get("loss_coefficient") is not None:
        return _get_value(immob, "K_IM", "loss_coefficient", default=1.0)

    thickness = d_im if d_im is not None else _get_value(immob, "d_IM", "d_im", default=1.0)
    diffusion = d_eff if d_eff is not None else _get_value(immob, "D_eff", "d_eff", default=1.0)
    if diffusion <= 0:
        return 0.0
    # Diffusion attenuation factor across IM layer.
    return math.exp(-(thickness * thickness) / diffusion)


def calculate_sensitivity(
    bre: Dict[str, Any],
    mem: Dict[str, Any],
    immob: Dict[str, Any],
    d_im: Optional[float] = None,
    d_eff: Optional[float] = None,
) -> float:
    sn_bre = _get_value(bre, "SN_BRE", "SN", "sensitivity", default=0.0)
    sn_mem = _get_value(mem, "SN_MEM", "SN", "sensitivity", default=0.0)
    k_im = calculate_k_im(immob, d_im=d_im, d_eff=d_eff)
    return sn_bre * sn_mem * k_im


def calculate_response_time(
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
    d_im: Optional[float] = None,
    d_eff: Optional[float] = None,
) -> float:
    tr_bre = _get_value(bre, "TR_BRE", "TR", "response_time", default=0.0)
    tr_mem = _get_value(mem, "TR_MEM", "TR", "response_time", default=0.0)
    thickness = d_im if d_im is not None else _get_value(immob, "d_IM", "d_im", default=1.0)
    diffusion = d_eff if d_eff is not None else _get_value(immob, "D_eff", "d_eff", default=1.0)
    diffusion_term = (thickness * thickness) / max(diffusion, 1e-12)
    return tr_bre + diffusion_term + tr_mem


def calculate_stability(
    analyte: Optional[Dict[str, Any]],
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
) -> float:
    st_ta = _get_value(analyte or {}, "ST_TA", "ST", "stability", default=float("inf"))
    st_bre = _get_value(bre, "ST_BRE", "ST", "stability", default=float("inf"))
    st_im = _get_value(immob, "ST_IM", "ST", "stability", default=float("inf"))
    st_mem = _get_value(mem, "ST_MEM", "ST", "stability", default=float("inf"))
    return min(st_ta, st_bre, st_im, st_mem)


def calculate_noise_sigma(
    mem: Dict[str, Any],
    i_read: Optional[float] = None,
    snr_mem: Optional[float] = None,
) -> float:
    i_value = i_read if i_read is not None else _get_value(mem, "I_read", "i_read", default=1.0)
    snr_value = snr_mem if snr_mem is not None else _get_value(mem, "SNR_MEM", "snr_mem", default=1.0)
    return i_value / max(snr_value, 1e-12)


def calculate_lod(
    bre: Dict[str, Any],
    mem: Dict[str, Any],
    sensitivity: Optional[float] = None,
    i_read: Optional[float] = None,
    snr_mem: Optional[float] = None,
    immob: Optional[Dict[str, Any]] = None,
) -> float:
    sn = sensitivity
    if sn is None:
        sn = calculate_sensitivity(bre, mem, immob or {})
    sigma_noise = calculate_noise_sigma(mem, i_read=i_read, snr_mem=snr_mem)
    return (3.0 * sigma_noise) / max(sn, 1e-12)


def calculate_dynamic_range(
    bre: Dict[str, Any],
    mem: Dict[str, Any],
    lod: Optional[float] = None,
    k_m: Optional[float] = None,
    c_max: Optional[float] = None,
) -> float:
    lod_value = lod if lod is not None else calculate_lod(bre, mem)
    if c_max is None:
        k_m_value = k_m if k_m is not None else _get_value(bre, "K_M", "k_m", default=1.0)
        c_max = 10.0 * k_m_value
    return c_max / max(lod_value, 1e-12)


def calculate_reproducibility(
    bre: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
    cv: Optional[float] = None,
) -> float:
    cv_value = cv if cv is not None else _get_value(mem, "CV", "cv", default=1.0)
    return 1.0 / max(cv_value, 1e-12)


def calculate_half_life(bre: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return min(
        _get_value(bre, "HL_BRE", "HL", "durability", default=float("inf")),
        _get_value(immob, "HL_IM", "HL", "durability", default=float("inf")),
        _get_value(mem, "HL_MEM", "HL", "durability", default=float("inf")),
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
        normalized = (value - min_value) / (max_value - min_value)
    else:
        normalized = (max_value - value) / (max_value - min_value)
    return max(0.0, min(1.0, normalized))


def compute_data_completeness_vector(structure: Dict[str, Any]) -> Tuple[Dict[str, int], float, str]:
    keys = [
        "SN_BRE",
        "SN_MEM",
        "K_IM",
        "d_IM",
        "D_eff",
        "TR_BRE",
        "TR_MEM",
        "ST_TA",
        "ST_BRE",
        "ST_IM",
        "ST_MEM",
        "I_read",
        "SNR_MEM",
        "K_M",
        "CV",
        "HL_BRE",
        "HL_IM",
        "HL_MEM",
    ]
    vector = {key: int(structure.get(key) is not None) for key in keys}
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
    sn_total = calculate_sensitivity(bre, mem, immob)
    lod_total = calculate_lod(bre, mem, sensitivity=sn_total, immob=immob)
    metrics = {
        "SN_total": sn_total,
        "TR_total": calculate_response_time(bre, immob, mem),
        "ST_total": calculate_stability(analyte, bre, immob, mem),
        "LOD_total": lod_total,
        "DR_total": calculate_dynamic_range(bre, mem, lod=lod_total),
        "RP_total": calculate_reproducibility(bre, immob, mem),
        "HL_total": calculate_half_life(bre, immob, mem),
    }
    metrics["PC_total"] = (
        _get_value(bre, "PC", "power_consumption", default=0.0)
        + _get_value(immob, "PC", "power_consumption", default=0.0)
        + _get_value(mem, "PC", "power_consumption", default=0.0)
    )
    return metrics
