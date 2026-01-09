from app.agent.intents import IntentType
from app.utils.merge import (
    merge_scope,
    merge_role_definition,
    merge_role_features,
    merge_system_features,
    merge_migration_strategy,
    merge_third_party_services,
    merge_non_functional,
    merge_project_description,
    merge_business_goals,
    merge_current_process,
    merge_data_entities,
    merge_integrations,
    merge_design,
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

    # 1. SCOPE - Hardcoded because it drives logic
    if intent_type in [IntentType.DEFINE_SCOPE, IntentType.SCOPE_CLARIFICATION, IntentType.SCOPE_INQUIRY]:
        return merge_scope(context, answer)

    # 2. STRUCTURAL DATA - Merge manually to ensure consistent lists
    if intent_type == IntentType.ROLE_DEFINITION:
        return merge_role_definition(context, answer)

    if intent_type == IntentType.ROLE_FEATURES:
        role = intent.get("role")
        return merge_role_features(context, role, answer)

    if intent_type == IntentType.SYSTEM_FEATURES:
        return merge_system_features(context, answer)

    if intent_type == IntentType.MIGRATION_STRATEGY:
        return merge_migration_strategy(context, answer)

    if intent_type == IntentType.THIRD_PARTY_SERVICES:
        return merge_third_party_services(context, answer)

    if intent_type == IntentType.COMPLIANCE_REQUIREMENTS:
        return merge_non_functional(context, "compliance", answer)

    if intent_type == IntentType.PROJECT_DESCRIPTION:
        return merge_project_description(context, answer)

    if intent_type == IntentType.BUSINESS_GOALS:
        return merge_business_goals(context, answer)

    if intent_type == IntentType.CURRENT_PROCESS:
        return merge_current_process(context, answer)

    if intent_type == IntentType.DATA_ENTITIES:
        return merge_data_entities(context, answer)

    if intent_type == IntentType.INTEGRATIONS:
        return merge_integrations(context, answer)

    if intent_type == IntentType.ADDITIONAL_INFO:
        return merge_additional_info(context, answer)

    # Design Routing
    if intent_type in [IntentType.DESIGN_PREFERENCES, IntentType.REFERENCE_URLS, IntentType.ASSETS_UPLOAD]:
        design_key = intent_type.lower()
        return merge_design(context, design_key, answer)

    # NFR Routing
    if intent_type in [IntentType.SECURITY_REQUIREMENTS, IntentType.PERFORMANCE_REQUIREMENTS, IntentType.TECH_STACK_PREFERENCE, IntentType.PROJECT_TIMELINE, IntentType.CONSTRAINTS]:
        nfr_key = intent_type.lower()
        return merge_non_functional(context, nfr_key, answer)

    return context
