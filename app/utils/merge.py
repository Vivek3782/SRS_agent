def merge_project_description(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context["project_description"] = answer.strip()
    return context


def merge_role_definition(context: dict, answer: str) -> dict:
    """
    Merge role definitions into context.
    """
    roles = context.setdefault("roles", {})
    for role in answer.split(","):
        role_name = role.strip()
        if role_name:
            roles.setdefault(role_name, {})

    return context


def merge_role_features(context: dict, role: str, answer: str) -> dict:
    if not answer or not role:
        return context

    features = [f.strip() for f in answer.split(",") if f.strip()]

    context.setdefault("roles", {})

    # Defensive: ensure role is a dictionary
    if role in context["roles"] and not isinstance(context["roles"][role], dict):
        context["roles"][role] = {}

    context["roles"].setdefault(role, {})

    # Defensive: ensure features is a list
    if "features" in context["roles"][role] and not isinstance(context["roles"][role]["features"], list):
        context["roles"][role]["features"] = []

    context["roles"][role].setdefault("features", [])

    context["roles"][role]["features"].extend(features)

    # deduplicate
    context["roles"][role]["features"] = list(
        set(context["roles"][role]["features"])
    )

    return context


def merge_system_features(context: dict, answer: str) -> dict:
    if not answer:
        return context

    features = [f.strip() for f in answer.split(",") if f.strip()]
    context.setdefault("system_features", [])
    context["system_features"].extend(features)

    context["system_features"] = list(set(context["system_features"]))
    return context


def merge_non_functional(context: dict, key: str, answer: str) -> dict:
    if not answer:
        return context

    context.setdefault("non_functional_requirements", {})
    context["non_functional_requirements"][key] = answer.strip()

    return context


def merge_additional_info(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context.setdefault("additional_notes", [])
    context["additional_notes"].append(answer.strip())

    return context
