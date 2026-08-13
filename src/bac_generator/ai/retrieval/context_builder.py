from bac_generator.schemas.retrieval import RetrievedChunk


class ContextBuilder:
    def build(
        self,
        chunks: list[RetrievedChunk],
        max_chunks: int = 5,
    ) -> str:
        if max_chunks <= 0:
            raise ValueError("max_chunks must be greater than zero.")

        if not chunks:
            return ""

        selected_chunks = chunks[:max_chunks]

        context_parts: list[str] = []

        for position, chunk in enumerate(
            selected_chunks,
            start=1,
        ):
            metadata_parts = [
                f"source={chunk.source}",
                f"topic={chunk.topic}",
                f"score={chunk.score:.4f}",
            ]

            if chunk.year is not None:
                metadata_parts.append(
                    f"year={chunk.year}"
                )

            if chunk.bac_section is not None:
                metadata_parts.append(
                    f"bac_section={chunk.bac_section}"
                )

            if chunk.exercise_type is not None:
                metadata_parts.append(
                    f"exercise_type={chunk.exercise_type}"
                )

            if chunk.difficulty is not None:
                metadata_parts.append(
                    f"difficulty={chunk.difficulty}"
                )

            metadata = ", ".join(metadata_parts)

            context_parts.append(
                "\n".join(
                    [
                        f"[REFERENCE {position}]",
                        f"Metadata: {metadata}",
                        "Content:",
                        chunk.text,
                    ]
                )
            )

        return "\n\n".join(context_parts)