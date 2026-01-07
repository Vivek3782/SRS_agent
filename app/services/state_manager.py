from datetime import datetime
from app.schemas.state import SessionState


def initialize_state(existing_state: dict | None, branding_data: dict | None = None) -> SessionState:
    if not existing_state:
        # Pre-fill context from Branding Data if available
        initial_context = {}
        if branding_data:
            # 1. Project Description from Description + Mission
            desc = branding_data.get("description", "")
            mission = branding_data.get("mission", "")
            full_desc = f"{desc}\n\nMission: {mission}".strip()
            if full_desc:
                initial_context["PROJECT_DESCRIPTION"] = full_desc

            # 2. Business Goals (Initial placeholder)
            name = branding_data.get("name", "")
            industry = branding_data.get("industry", "")
            if name or industry:
                initial_context[
                    "BUSINESS_GOALS"] = f"Company: {name}\nIndustry: {industry}\n(Please refine specific business goals)"

            # 3. Design / Additional Info
            visuals = branding_data.get("visual_references", [])
            refresh_urls = branding_data.get("agency_refresh_urls", [])
            tone = branding_data.get("brand_voice", "")

            design_notes = []
            if tone:
                design_notes.append(f"Brand Voice: {tone}")
            if refresh_urls:
                design_notes.append(
                    f"Reference URLs: {', '.join(refresh_urls)}")
            if visuals:
                design_notes.append(
                    f"Visual Assets Provided: {len(visuals)} items")

            if design_notes:
                initial_context["ADDITIONAL_INFO"] = "Design Guidelines:\n" + \
                    "\n".join(design_notes)

        return SessionState(
            phase="INIT",
            context=initial_context,
            additional_questions_asked=0,
            history=[]
        )
    return SessionState(**existing_state)


def build_ask_state(
    *,
    phase: str,
    context: dict,
    question: str,
    pending_intent: dict | None,
    additional_questions_asked: int,
    history: list
) -> dict:
    state = SessionState(
        phase=phase,
        context=context,
        last_question={
            "text": question,
            "asked_at": datetime.utcnow().isoformat()
        },
        pending_intent=pending_intent,
        additional_questions_asked=additional_questions_asked,
        history=history
    )
    return state.model_dump()
