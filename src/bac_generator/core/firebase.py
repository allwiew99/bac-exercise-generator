import firebase_admin

from bac_generator.core.config import settings


def initialize_firebase() -> None:
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(
            options={
                "projectId": settings.firebase_project_id,
            }
        )