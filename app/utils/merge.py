def merge_project_description(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context["project_description"] = answer.strip()
    return context


def merge_scope(context: dict, answer: str) -> dict:
    if not answer:
        return context

    # Simple heuristic if the agent didn't extract the keyword perfectly
    if "update" in answer.lower() or "partial" in answer.lower() or "refactor" in answer.lower():
        context["project_scope"] = "PARTIAL_UPDATE"
    elif "new" in answer.lower() or "scratch" in answer.lower():
        context["project_scope"] = "NEW_BUILD"
    else:
        # Default fallback, or store the raw answer to let agent decide next turn
        context["project_scope"] = "UNKNOWN"
        context["scope_details"] = answer.strip()

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


def merge_business_goals(context: dict, answer: str) -> dict:
    if not answer:
        return context
    context.setdefault("business_goals", [])
    context["business_goals"].append(answer.strip())
    return context


def merge_current_process(context: dict, answer: str) -> dict:
    if not answer:
        return context
    context["current_process"] = answer.strip()
    return context


def merge_role_features(context: dict, role: str, answer: str) -> dict:
    if not answer or not role:
        return context

    features = [f.strip() for f in answer.split(",") if f.strip()]

    context.setdefault("roles", {})

    if role in context["roles"] and not isinstance(context["roles"][role], dict):
        context["roles"][role] = {}

    context["roles"].setdefault(role, {})

    if "features" in context["roles"][role] and not isinstance(context["roles"][role]["features"], list):
        context["roles"][role]["features"] = []

    context["roles"][role].setdefault("features", [])

    context["roles"][role]["features"].extend(features)

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


def merge_data_entities(context: dict, answer: str) -> dict:
    if not answer:
        return context
    context["data_entities"] = answer.strip()
    return context


def merge_integrations(context: dict, answer: str) -> dict:
    if not answer:
        return context
    context.setdefault("integrations", [])
    context["integrations"].append(answer.strip())
    return context


def merge_design(context: dict, key: str, answer: str) -> dict:
    if not answer:
        return context
    context.setdefault("design_requirements", {})
    # For lists like URLs, try to split if comma separated
    if key in ["reference_urls", "assets"]:
        current_list = context["design_requirements"].get(key, [])
        new_items = [item.strip()
                     for item in answer.split(",") if item.strip()]
        context["design_requirements"][key] = current_list + new_items
    else:
        context["design_requirements"][key] = answer.strip()
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
