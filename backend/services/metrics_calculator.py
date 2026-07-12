from typing import Any, Dict

from domain.metrics import (
    calculate_dynamic_range,
    calculate_half_life,
    calculate_lod,
    calculate_reproducibility,
    calculate_response_time,
    calculate_sensitivity,
    calculate_stability,
)


def calculate_sn_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return calculate_sensitivity(bio, mem, immob)


def calculate_tr_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return calculate_response_time(bio, immob, mem)


def calculate_st_total(
    bio: Dict[str, Any],
    immob: Dict[str, Any],
    mem: Dict[str, Any],
    analyte: Dict[str, Any] | None = None,
) -> float:
    return calculate_stability(analyte, bio, immob, mem)


def calculate_lod_total(bio: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return calculate_lod(bio, mem)


def calculate_dr_total(bio: Dict[str, Any], mem: Dict[str, Any]) -> float:
    lod = calculate_lod_total(bio, mem)
    return calculate_dynamic_range(bio, mem, lod=lod)


def calculate_pc_total(analyte: Dict[str, Any], bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return (
        analyte.get("power_consumption", analyte.get("PC", 0))
        + bio.get("power_consumption", bio.get("PC", 0))
        + immob.get("power_consumption", immob.get("PC", 0))
        + mem.get("power_consumption", mem.get("PC", 0))
    )


def calculate_rp_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any], cv: float | None = None) -> float:
    return calculate_reproducibility(bio, immob, mem, cv=cv)


def calculate_hl_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return calculate_half_life(bio, immob, mem)
