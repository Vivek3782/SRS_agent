from app.services.redis_service import redis_service
from app.schemas.branding import BrandingState

class BrandingService:
    def get_state(self, session_id: str) -> BrandingState:
        """
        Fetches 'branding:session:{id}' from Redis.
        Returns empty state if new.
        """
        key = f"branding:session:{session_id}"
        data = redis_service.client.get(key)
        
        if not data:
            return BrandingState()
            
        return BrandingState.model_validate_json(data)

    def save_state(self, session_id: str, state: BrandingState):
        """
        Saves state to 'branding:session:{id}'
        """
        key = f"branding:session:{session_id}"
        redis_service.client.set(key, state.model_dump_json())

    def delete_state(self, session_id: str):
        key = f"branding:session:{session_id}"
        redis_service.client.delete(key)

branding_service = BrandingService()