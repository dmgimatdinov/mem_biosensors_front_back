from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class CompatibilityEngineV2:
    """Расширенный движок совместимости с двухэтапной валидацией."""

    APPLICATION_PROFILES = {"PoC", "LoC", "Clinical_Diagnostics"}

    _ADHESION_MAP = {
        "слабая": 0.3,
        "низкая": 0.3,
        "средняя": 0.6,
        "хорошая": 0.8,
        "высокая": 1.0,
        "отличная": 1.2,
    }

    _SOLUBILITY_MAP = {
        "водорастворимый": 12.0,
        "органический": 8.0,
        "нерастворимый": 2.0,
    }

    def __init__(self) -> None:
        self._last_stage1_trace: List[str] = []

    @staticmethod
    def _get_value(source: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in source and source[key] is not None:
                return source[key]
        return None

    @classmethod
    def _to_float(cls, source: Dict[str, Any], *keys: str, default: Optional[float] = None) -> Optional[float]:
        value = cls._get_value(source, *keys)
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_bool(source: Dict[str, Any], *keys: str, default: bool = False) -> bool:
        for key in keys:
            if key in source and source[key] is not None:
                value = source[key]
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.strip().lower() in {"1", "true", "yes", "y", "да"}
                if isinstance(value, (int, float)):
                    return bool(value)
        return default

    @staticmethod
    def _extract_structure(structure: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        ta = structure.get("TA") or structure.get("analyte") or structure.get("ta") or {}
        bre = structure.get("BRE") or structure.get("bio_layer") or structure.get("bio") or {}
        im = structure.get("IM") or structure.get("immobilization_layer") or structure.get("immob") or {}
        mem = structure.get("MEM") or structure.get("memristive_layer") or structure.get("mem") or {}
        return ta, bre, im, mem

    @staticmethod
    def _format_range(name: str, min_v: float, max_v: float) -> str:
        return f"{name} {min_v:.1f}-{max_v:.1f}"

    @staticmethod
    def _ranges_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
        return max(a_min, b_min) <= min(a_max, b_max)

    def check_pH_compatibility(
        self,
        ta: Dict[str, Any],
        bre: Dict[str, Any],
        im: Dict[str, Any],
        mem: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        ta_min = self._to_float(ta, "PH_Min", "ph_min", default=0.0)
        ta_max = self._to_float(ta, "PH_Max", "ph_max", default=14.0)
        bre_min = self._to_float(bre, "PH_Min", "ph_min", default=0.0)
        bre_max = self._to_float(bre, "PH_Max", "ph_max", default=14.0)
        im_min = self._to_float(im, "PH_Min", "ph_min", default=0.0)
        im_max = self._to_float(im, "PH_Max", "ph_max", default=14.0)
        mem_min = self._to_float(mem, "PH_Min", "ph_min", default=0.0)
        mem_max = self._to_float(mem, "PH_Max", "ph_max", default=14.0)

        pairs = [
            ("TA", ta_min, ta_max, "BRE", bre_min, bre_max),
            ("TA", ta_min, ta_max, "IM", im_min, im_max),
            ("TA", ta_min, ta_max, "MEM", mem_min, mem_max),
            ("BRE", bre_min, bre_max, "IM", im_min, im_max),
            ("BRE", bre_min, bre_max, "MEM", mem_min, mem_max),
            ("IM", im_min, im_max, "MEM", mem_min, mem_max),
        ]
        for left_name, left_min, left_max, right_name, right_min, right_max in pairs:
            if not self._ranges_overlap(left_min, left_max, right_min, right_max):
                reason = (
                    f"pH-несовместимость: {left_name} требует pH {left_min:.1f}-{left_max:.1f}, "
                    f"{right_name} работает при pH {right_min:.1f}-{right_max:.1f}"
                )
                return False, reason

        return True, None

    def check_analyte_thermal_stability(
        self,
        ta: Dict[str, Any],
        bre: Dict[str, Any],
        im: Dict[str, Any],
        mem: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        ta_t_max = self._to_float(ta, "T_Max", "t_max", default=0.0)
        layer_t_max = max(
            self._to_float(bre, "T_Max", "t_max", default=0.0),
            self._to_float(im, "T_Max", "t_max", default=0.0),
            self._to_float(mem, "T_Max", "t_max", default=0.0),
        )
        if layer_t_max > ta_t_max:
            return False, (
                "Термическая деградация аналита: "
                f"макс. рабочая температура слоёв {layer_t_max:.1f} выше T_Max аналита {ta_t_max:.1f}"
            )
        return True, None

    def check_layer_temperature_compatibility(
        self,
        bre: Dict[str, Any],
        im: Dict[str, Any],
        mem: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        bre_min = self._to_float(bre, "T_Min", "t_min", default=-273.0)
        bre_max = self._to_float(bre, "T_Max", "t_max", default=1000.0)
        im_min = self._to_float(im, "T_Min", "t_min", default=-273.0)
        im_max = self._to_float(im, "T_Max", "t_max", default=1000.0)
        mem_min = self._to_float(mem, "T_Min", "t_min", default=-273.0)
        mem_max = self._to_float(mem, "T_Max", "t_max", default=1000.0)

        t_min = max(bre_min, im_min, mem_min)
        t_max = min(bre_max, im_max, mem_max)
        if t_min > t_max:
            return False, (
                "Температурная несовместимость слоёв: "
                f"BRE {self._format_range('T', bre_min, bre_max)}, "
                f"IM {self._format_range('T', im_min, im_max)}, "
                f"MEM {self._format_range('T', mem_min, mem_max)}"
            )
        return True, None

    def check_mechanical_compatibility(
        self,
        im: Dict[str, Any],
        mem: Dict[str, Any],
        delta_max: float = 0.5,
    ) -> Tuple[bool, Optional[str]]:
        mp_im = self._to_float(im, "MP", "young_modulus", "MP_IM", default=0.0)
        mp_mem = self._to_float(mem, "MP", "young_modulus", "MP_MEM", default=0.0)
        delta = abs(mp_im - mp_mem)
        if delta > delta_max:
            return False, (
                f"Механическая несовместимость: |MP_IM - MP_MEM| = {delta:.1f} ГПа > {delta_max:.1f} ГПа"
            )
        return True, None

    def check_adhesion_solubility(
        self,
        im: Dict[str, Any],
        adh_min: float = 0.5,
        sol_max: float = 10.0,
    ) -> Tuple[bool, Optional[str]]:
        adh_raw = self._get_value(im, "Adh_IM", "Adh", "adhesion")
        sol_raw = self._get_value(im, "Sol_IM", "Sol", "solubility")

        if isinstance(adh_raw, str):
            adh = self._ADHESION_MAP.get(adh_raw.strip().lower())
        else:
            adh = self._to_float(im, "Adh_IM", "Adh", "adhesion", default=None)

        if isinstance(sol_raw, str):
            sol = self._SOLUBILITY_MAP.get(sol_raw.strip().lower())
        else:
            sol = self._to_float(im, "Sol_IM", "Sol", "solubility", default=None)

        if adh is not None and adh < adh_min:
            return False, f"Низкая адгезия IM: {adh:.1f} МПа < {adh_min:.1f} МПа"

        if sol is not None and sol > sol_max:
            return False, f"Высокая растворимость IM: {sol:.1f} > {sol_max:.1f}"

        return True, None

    def validate_stage1(self, structure: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Иерархическая проверка Stage1 с ранним отсечением по pH."""
        ta, bre, im, mem = self._extract_structure(structure)
        failed: List[str] = []
        self._last_stage1_trace = []

        checks = [
            ("check_pH_compatibility", lambda: self.check_pH_compatibility(ta, bre, im, mem), True),
            ("check_analyte_thermal_stability", lambda: self.check_analyte_thermal_stability(ta, bre, im, mem), False),
            ("check_layer_temperature_compatibility", lambda: self.check_layer_temperature_compatibility(bre, im, mem), False),
            ("check_mechanical_compatibility", lambda: self.check_mechanical_compatibility(im, mem), False),
            ("check_adhesion_solubility", lambda: self.check_adhesion_solubility(im), False),
        ]

        for name, callback, early_stop in checks:
            self._last_stage1_trace.append(name)
            ok, reason = callback()
            if not ok:
                failed.append(reason or name)
                if early_stop:
                    return False, failed

        return len(failed) == 0, failed

    def validate_stage2(
        self,
        structure: Dict[str, Any],
        application_profile: str,
    ) -> Tuple[bool, List[str]]:
        if application_profile not in self.APPLICATION_PROFILES:
            raise ValueError("application_profile must be one of: PoC, LoC, Clinical_Diagnostics")

        ta, bre, im, mem = self._extract_structure(structure)
        failed: List[str] = []

        pc = self._to_float(structure, "PC", "pc", "PC_total", "pc_total", default=None)
        if pc is None:
            pc = sum(
                value
                for value in [
                    self._to_float(ta, "PC", "power_consumption", default=0.0),
                    self._to_float(bre, "PC", "power_consumption", default=0.0),
                    self._to_float(im, "PC", "power_consumption", default=0.0),
                    self._to_float(mem, "PC", "power_consumption", default=0.0),
                ]
            )

        tr = self._to_float(structure, "TR", "tr", "TR_total", "tr_total", "response_time", default=None)
        if tr is None:
            tr = sum(
                value
                for value in [
                    self._to_float(bre, "TR", "response_time", default=0.0),
                    self._to_float(im, "TR", "response_time", default=0.0),
                    self._to_float(mem, "TR", "response_time", default=0.0),
                ]
            )

        iso_10993 = self._to_bool(structure, "iso_10993", "ISO_10993", default=False)
        thermal_resistant = self._to_bool(structure, "temperature_resistant", "thermal_resistance", default=True)

        if application_profile == "PoC":
            if pc >= 10.0:
                failed.append(f"PoC: энергопотребление {pc:.1f} мВт >= 10.0 мВт")
            if not iso_10993:
                failed.append("PoC: отсутствует подтверждение ISO 10993")
            if not thermal_resistant:
                failed.append("PoC: недостаточная термоустойчивость")

        if application_profile == "LoC":
            pdms_ok = self._to_bool(structure, "pdms_compatible", "PDMS_compatible", default=False)
            leakage_ul = self._to_float(structure, "leakage_ul", "leakage_uL", default=999.0)
            if not pdms_ok:
                failed.append("LoC: несовместимость с PDMS")
            if leakage_ul >= 1.0:
                failed.append(f"LoC: утечки {leakage_ul:.2f} мкл >= 1.00 мкл")

        if application_profile == "Clinical_Diagnostics":
            if not iso_10993:
                failed.append("Clinical: отсутствует подтверждение ISO 10993")
            if tr >= 15.0:
                failed.append(f"Clinical: TR {tr:.1f} мин >= 15.0 мин")

            stability_months = self._to_float(structure, "stability_months", "stability_mo", default=None)
            if stability_months is None:
                st_days = self._to_float(structure, "ST", "stability", "ST_total", "st_total", default=0.0)
                stability_months = st_days / 30.0
            if stability_months <= 6.0:
                failed.append(f"Clinical: стабильность {stability_months:.1f} мес <= 6.0 мес")

        return len(failed) == 0, failed

    def build_compatibility_index(
        self,
        analytes: List[Dict[str, Any]],
        bio_layers: List[Dict[str, Any]],
        immob_layers: List[Dict[str, Any]],
        mem_layers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Предрасчёт индексных наборов:
        Index(IM_i) = {BRE_j} x {MEM_k}.

        Возвращает также оценку сложности до/после индексации.
        """
        index: Dict[str, Dict[str, List[str]]] = {}
        pairs_count = 0

        for im in immob_layers:
            im_id = str(self._get_value(im, "IM_ID", "im_id", "id") or "IM_UNKNOWN")
            bre_ids: List[str] = []
            mem_ids: List[str] = []

            im_t_min = self._to_float(im, "T_Min", "t_min", default=-273.0)
            im_t_max = self._to_float(im, "T_Max", "t_max", default=1000.0)

            for bre in bio_layers:
                bre_t_min = self._to_float(bre, "T_Min", "t_min", default=-273.0)
                bre_t_max = self._to_float(bre, "T_Max", "t_max", default=1000.0)
                if not self._ranges_overlap(bre_t_min, bre_t_max, im_t_min, im_t_max):
                    continue
                bre_ids.append(str(self._get_value(bre, "BRE_ID", "bre_id", "id") or "BRE_UNKNOWN"))

            for mem in mem_layers:
                ok_mech, _ = self.check_mechanical_compatibility(im, mem)
                if not ok_mech:
                    continue
                ok_adh, _ = self.check_adhesion_solubility(im)
                if not ok_adh:
                    continue
                mem_ids.append(str(self._get_value(mem, "MEM_ID", "mem_id", "id") or "MEM_UNKNOWN"))

            index[im_id] = {
                "bre_ids": sorted(set(bre_ids)),
                "mem_ids": sorted(set(mem_ids)),
            }
            pairs_count += len(index[im_id]["bre_ids"]) * len(index[im_id]["mem_ids"])

        base_complexity = len(analytes) * len(bio_layers) * len(immob_layers) * len(mem_layers)
        indexed_complexity = len(analytes) * max(1, pairs_count)

        return {
            "index": index,
            "complexity": {
                "before": f"O(N^4)",
                "after": f"O(N^2 * k)",
                "baseline_candidates": base_complexity,
                "indexed_candidates": indexed_complexity,
            },
        }

    @property
    def last_stage1_trace(self) -> List[str]:
        return list(self._last_stage1_trace)
