from typing import Any, Dict


def calculate_sn_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return bio.get("sensitivity", bio.get("SN", 0)) * mem.get("sensitivity", mem.get("SN", 0)) * immob.get("loss_coefficient", immob.get("K_IM", 1))


def calculate_tr_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return (
        bio.get("response_time", bio.get("TR", 0))
        + immob.get("response_time", immob.get("TR", 0))
        + mem.get("response_time", mem.get("TR", 0))
    )


def calculate_st_total(bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return min(
        bio.get("stability", bio.get("ST", 0)),
        immob.get("stability", immob.get("ST", 0)),
        mem.get("stability", mem.get("ST", 0)),
    )


def calculate_lod_total(bio: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return max(bio.get("lod", bio.get("LOD", 0)), mem.get("lod", mem.get("LOD", 0)))


def calculate_dr_total(bio: Dict[str, Any], mem: Dict[str, Any]) -> float:
    bio_min = bio.get("dr_min", bio.get("DR_Min", 0))
    bio_max = bio.get("dr_max", bio.get("DR_Max", float("inf")))
    mem_min = mem.get("dr_min", mem.get("DR_Min", 0))
    mem_max = mem.get("dr_max", mem.get("DR_Max", float("inf")))
    return max(0, min(bio_max, mem_max) - max(bio_min, mem_min))


def calculate_pc_total(analyte: Dict[str, Any], bio: Dict[str, Any], immob: Dict[str, Any], mem: Dict[str, Any]) -> float:
    return (
        analyte.get("power_consumption", analyte.get("PC", 0))
        + bio.get("power_consumption", bio.get("PC", 0))
        + immob.get("power_consumption", immob.get("PC", 0))
        + mem.get("power_consumption", mem.get("PC", 0))
    )
