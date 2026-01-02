from app.agent.intents import IntentType
from app.utils.merge import (
    merge_project_description,
    merge_role_definition,
    merge_role_features,
    merge_system_features,
    merge_non_functional,
    merge_additional_info,
)

def consume_intent(
    *,
    intent: dict | None,
    context: dict,
    answer
) -> dict:
    """
    Apply the user's answer to context based on pending_intent.
    """

    if not intent or not answer:
        return context

    intent_type = intent.get("type")

    if intent_type == IntentType.PROJECT_DESCRIPTION:
        return merge_project_description(context, answer)

    if intent_type == IntentType.ROLE_DEFINITION:
        return merge_role_definition(context, answer)

    if intent_type == IntentType.ROLE_FEATURES:
        role = intent.get("role")
        return merge_role_features(context, role, answer)

    if intent_type == IntentType.SYSTEM_FEATURES:
        return merge_system_features(context, answer)

    if intent_type == IntentType.SECURITY_REQUIREMENTS:
        return merge_non_functional(context, "security", answer)

    if intent_type == IntentType.PERFORMANCE_REQUIREMENTS:
        return merge_non_functional(context, "performance", answer)

    if intent_type == IntentType.CONSTRAINTS:
        return merge_non_functional(context, "constraints", answer)

    if intent_type == IntentType.ADDITIONAL_INFO:
        return merge_additional_info(context, answer)

    return context
