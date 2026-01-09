def merge_project_description(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context["project_description"] = str(answer).strip()
    return context


def merge_migration_strategy(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context["migration_strategy"] = str(answer).strip()
    return context


def merge_scope(context: dict, answer: str) -> dict:
    if not answer:
        return context

    ans_str = str(answer).lower()
    # Simple heuristic if the agent didn't extract the keyword perfectly
    if "update" in ans_str or "partial" in ans_str or "refactor" in ans_str:
        context["project_scope"] = "PARTIAL_UPDATE"
    elif "new" in ans_str or "scratch" in ans_str:
        context["project_scope"] = "NEW_BUILD"
    else:
        # Default fallback, or store the raw answer to let agent decide next turn
        context["project_scope"] = "UNKNOWN"
        context["scope_details"] = str(answer).strip()

    return context


def merge_role_definition(context: dict, answer: str) -> dict:
    """
    Merge role definitions into context.
    """
    if "roles" in context and not isinstance(context["roles"], dict):
        context["roles"] = {}

    roles = context.setdefault("roles", {})

    # Handle list or string answer
    if isinstance(answer, list):
        role_list = [str(r).strip() for r in answer if r]
    else:
        role_list = [str(r).strip()
                     for r in str(answer).split(",") if r.strip()]

    for role_name in role_list:
        if role_name:
            roles.setdefault(role_name, {})

    return context


def merge_business_goals(context: dict, answer: str) -> dict:
    if not answer:
        return context

    if "business_goals" in context and not isinstance(context["business_goals"], list):
        context["business_goals"] = []

    context.setdefault("business_goals", [])

    if isinstance(answer, list):
        context["business_goals"].extend([str(g).strip() for g in answer if g])
    else:
        context["business_goals"].append(str(answer).strip())

    # Deduplicate
    context["business_goals"] = list(dict.fromkeys(context["business_goals"]))
    return context


def merge_current_process(context: dict, answer: str) -> dict:
    if not answer:
        return context
    context["current_process"] = str(answer).strip()
    return context


def merge_role_features(context: dict, role: str, answer: str) -> dict:
    if not answer or not role:
        return context

    # Extract features safely
    if isinstance(answer, list):
        features = answer
    elif isinstance(answer, dict):
        # AI sent a dict? Take values or names
        features = list(answer.values()) if answer else []
    else:
        features = [f.strip() for f in str(answer).split(",") if f.strip()]

    context.setdefault("roles", {})
    if not isinstance(context["roles"], dict):
        context["roles"] = {}

    if role not in context["roles"] or not isinstance(context["roles"][role], dict):
        context["roles"][role] = {}

    # Ensure ui_features is a list
    if "ui_features" not in context["roles"][role] or not isinstance(context["roles"][role]["ui_features"], list):
        context["roles"][role]["ui_features"] = []

    # Merge and deduplicate (using dict.fromkeys for hashable/unhashable mix safety if needed,
    # but set() is usually fine if we convert to strings)
    for f in features:
        if f not in context["roles"][role]["ui_features"]:
            context["roles"][role]["ui_features"].append(f)

    return context


def merge_system_features(context: dict, answer: str) -> dict:
    if not answer:
        return context

    if isinstance(answer, list):
        features = answer
    else:
        features = [f.strip() for f in str(answer).split(",") if f.strip()]

    if "system_features" not in context or not isinstance(context["system_features"], list):
        context["system_features"] = []

    for f in features:
        if f not in context["system_features"]:
            context["system_features"].append(f)

    return context


def merge_data_entities(context: dict, answer: str) -> dict:
    if not answer:
        return context

    if "data_entities" not in context or not isinstance(context["data_entities"], list):
        context["data_entities"] = []

    if isinstance(answer, list):
        context["data_entities"].extend([str(e).strip() for e in answer if e])
    else:
        context["data_entities"].append(str(answer).strip())

    context["data_entities"] = list(dict.fromkeys(context["data_entities"]))
    return context


def merge_integrations(context: dict, answer: str) -> dict:
    if not answer:
        return context

    if "integrations" not in context or not isinstance(context["integrations"], list):
        context["integrations"] = []

    if isinstance(answer, list):
        context["integrations"].extend([str(i).strip() for i in answer if i])
    else:
        context["integrations"].append(str(answer).strip())

    context["integrations"] = list(dict.fromkeys(context["integrations"]))
    return context


def merge_third_party_services(context: dict, answer: str) -> dict:
    if not answer:
        return context

    if "third_party_services" not in context or not isinstance(context["third_party_services"], list):
        context["third_party_services"] = []

    if isinstance(answer, list):
        new_services = [str(s).strip() for s in answer if s]
    else:
        new_services = [s.strip() for s in str(answer).split(",") if s.strip()]

    for s in new_services:
        if s not in context["third_party_services"]:
            context["third_party_services"].append(s)

    return context


def merge_design(context: dict, key: str, answer: str) -> dict:
    if not answer:
        return context

    context.setdefault("design_requirements", {})
    if not isinstance(context["design_requirements"], dict):
        context["design_requirements"] = {}

    current_val = context["design_requirements"].get(key, [])

    # Some design keys should be strings (like current_app_url), others lists
    list_keys = ["design_preferences", "inspiration_urls",
                 "assets_upload", "reference_urls"]

    if key in list_keys:
        if not isinstance(current_val, list):
            current_val = [current_val] if current_val else []

        if isinstance(answer, list):
            new_items = answer
        else:
            new_items = [item.strip()
                         for item in str(answer).split(",") if item.strip()]

        for item in new_items:
            if item not in current_val:
                current_val.append(item)
        context["design_requirements"][key] = current_val
    else:
        # String key (e.g. current_app_url)
        context["design_requirements"][key] = str(answer).strip()

    return context


def merge_non_functional(context: dict, key: str, answer: str) -> dict:
    if not answer:
        return context

    context.setdefault("non_functional_requirements", {})
    if not isinstance(context["non_functional_requirements"], dict):
        context["non_functional_requirements"] = {}

    context["non_functional_requirements"][key] = str(answer).strip()

    return context


def merge_additional_info(context: dict, answer: str) -> dict:
    if not answer:
        return context

    context.setdefault("additional_notes", [])
    if not isinstance(context["additional_notes"], list):
        context["additional_notes"] = []

    if isinstance(answer, list):
        context["additional_notes"].extend(
            [str(n).strip() for n in answer if n])
    else:
        context["additional_notes"].append(str(answer).strip())

    return context
