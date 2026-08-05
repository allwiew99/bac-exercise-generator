from sqlalchemy.ext.asyncio import AsyncSession


class ExerciseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session