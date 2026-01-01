def merge_project_description(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context["project_description"] = answer.strip()
    return context


def merge_role_definition(context: dict, answer: str) -> dict:
    if not answer:
        return context

    roles = [r.strip() for r in answer.split(",") if r.strip()]
    context.setdefault("roles", {})

    for role in roles:
        context["roles"].setdefault(role.lower(), {})

    return context


def merge_role_features(context: dict, role: str, answer: str) -> dict:
    if not answer or not role:
        return context

    features = [f.strip() for f in answer.split(",") if f.strip()]

    context.setdefault("roles", {})
    context["roles"].setdefault(role, {})
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
