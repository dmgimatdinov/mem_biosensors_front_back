from typing import Any, Dict


def calculate_score(metrics: Dict[str, Any]) -> float:
    sn_total = float(metrics.get("sn_total", metrics.get("SN_total", 0)))
    tr_total = float(metrics.get("tr_total", metrics.get("TR_total", 0)))
    st_total = float(metrics.get("st_total", metrics.get("ST_total", 0)))
    lod_total = float(metrics.get("lod_total", metrics.get("LOD_total", 0)))
    dr_total = float(metrics.get("dr_total", metrics.get("DR_total", 0)))
    pc_total = float(metrics.get("pc_total", metrics.get("PC_total", 0)))

    sn_score = min(sn_total / 20000.0, 1.0)
    tr_score = max(0.0, 1.0 - min(tr_total / 3600.0, 1.0))
    st_score = min(st_total / 365.0, 1.0)
    lod_score = max(0.0, 1.0 - min(lod_total / 50000.0, 1.0))
    dr_score = min(dr_total / 1000.0, 1.0)
    pc_score = max(0.0, 1.0 - min(pc_total / 2000.0, 1.0))

    score = (
        4.0 * sn_score
        + 2.0 * tr_score
        + 1.5 * st_score
        + 1.0 * lod_score
        + 1.0 * dr_score
        + 0.5 * pc_score
    )
    return max(0.0, min(10.0, score))
