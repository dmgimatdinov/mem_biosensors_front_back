from typing import Dict, Set


ROLE_DESIGNER = "Designer"
ROLE_KB_ADMIN = "KB_Admin"
ROLE_VALIDATION_SPECIALIST = "Validation_Specialist"
ROLE_SYSTEM = "system"


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_DESIGNER: {
        "synthesis",
        "analysis",
        "export",
        "projects",
    },
    ROLE_KB_ADMIN: {
        "passports",
        "versioning",
        "audit",
        "users",
        "api_keys",
        "analysis",
        "export",
    },
    ROLE_VALIDATION_SPECIALIST: {
        "validation",
        "experimental_import",
        "analysis",
    },
    ROLE_SYSTEM: {
        "synthesis",
        "analysis",
        "export",
        "projects",
        "passports",
        "versioning",
        "audit",
        "users",
        "api_keys",
        "validation",
        "experimental_import",
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_role_or_system(role: str, required_role: str) -> bool:
    return role == required_role or role == ROLE_SYSTEM
