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
from app.agent.intents import IntentType
import logging

logger = logging.getLogger(__name__)


def consume_intent(
    *,
    intent: dict | None,
    context: dict,
    answer
) -> dict:
    """
    Apply the user's answer to context based on pending_intent.
    Handles 'Skip' logic to force 'Not Provided' entries.
    """

    if not intent or not answer:
        return context

    # --- NEW: DETECT SKIP/UNKNOWN ANSWERS ---
    skip_keywords = {"i don't know", "no", "none", "skip",
                     "unsure", "unknown", "n/a", "not applicable"}
    cleaned_answer = str(answer).strip().lower()

    # If the user skips, we force a specific placeholder string.
    # The merge functions will treat this as a valid entry, stopping the loop.
    effective_answer = answer
    if cleaned_answer in skip_keywords or len(cleaned_answer) < 2:
        effective_answer = "Not Provided"
    # ----------------------------------------

    intent_type = intent.get("type")

    # 1. SCOPE
    if intent_type in [IntentType.DEFINE_SCOPE, IntentType.SCOPE_CLARIFICATION, IntentType.SCOPE_INQUIRY]:
        return merge_scope(context, effective_answer)

    # 2. STRUCTURAL DATA
    if intent_type == IntentType.ROLE_DEFINITION:
        return merge_role_definition(context, effective_answer)

    if intent_type == IntentType.ROLE_FEATURES:
        role = intent.get("role")
        if not role:
            logger.error(
                f"CRITICAL: Received ROLE_FEATURES intent but 'role' is missing. Answer '{answer}' was DROPPED.")
            return context
        return merge_role_features(context, role, effective_answer)

    if intent_type == IntentType.SYSTEM_FEATURES:
        return merge_system_features(context, effective_answer)

    if intent_type == IntentType.SCREENS_PAGES:
        # Merge screens/pages as a list
        screens = context.get("screens_pages", [])
        if isinstance(screens, str):
            screens = [screens] if screens and screens != "Not Provided" else []

        # Parse the answer - could be comma-separated or a single page
        if effective_answer and effective_answer != "Not Provided":
            new_pages = [p.strip() for p in str(effective_answer).replace(
                "\n", ",").split(",") if p.strip()]
            for page in new_pages:
                if page not in screens:
                    screens.append(page)

        context["screens_pages"] = screens if screens else "Not Provided"
        return context

    if intent_type == IntentType.MIGRATION_STRATEGY:
        return merge_migration_strategy(context, effective_answer)

    if intent_type == IntentType.THIRD_PARTY_SERVICES:
        return merge_third_party_services(context, effective_answer)

    if intent_type == IntentType.COMPLIANCE_REQUIREMENTS:
        return merge_non_functional(context, "compliance", effective_answer)

    if intent_type == IntentType.PROJECT_DESCRIPTION:
        return merge_project_description(context, effective_answer)

    if intent_type == IntentType.BUSINESS_GOALS:
        return merge_business_goals(context, effective_answer)

    if intent_type == IntentType.CURRENT_PROCESS:
        return merge_current_process(context, effective_answer)

    if intent_type == IntentType.DATA_ENTITIES:
        return merge_data_entities(context, effective_answer)

    if intent_type == IntentType.INTEGRATIONS:
        return merge_integrations(context, effective_answer)

    if intent_type == IntentType.ADDITIONAL_INFO:
        return merge_additional_info(context, effective_answer)

    # Design Routing
    if intent_type in [IntentType.DESIGN_PREFERENCES, IntentType.REFERENCE_URLS, IntentType.INSPIRATION_URLS, IntentType.CURRENT_APP_URL, IntentType.ASSETS_UPLOAD]:
        design_key = intent_type.lower()
        return merge_design(context, design_key, effective_answer)

    # NFR Routing
    if intent_type in [IntentType.SECURITY_REQUIREMENTS, IntentType.PERFORMANCE_REQUIREMENTS, IntentType.TECH_STACK_PREFERENCE]:
        nfr_key = intent_type.lower()
        return merge_non_functional(context, nfr_key, effective_answer)

    # Logistical Routing
    if intent_type in [IntentType.PROJECT_TIMELINE, IntentType.CONSTRAINTS, IntentType.BUDGET]:
        context[intent_type.lower()] = str(effective_answer).strip()
        return context

    return context
