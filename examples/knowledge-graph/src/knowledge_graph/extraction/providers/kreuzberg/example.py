import asyncio
import sys

from kreuzberg import (
    ChunkingConfig,
    ExtractionConfig,
    KeywordAlgorithm,
    KeywordConfig,
    extract_file,
)


class DocumentTagger:
    def __init__(self, num_tags: int = 5, max_tokens: int = 8191):
        self.config: ExtractionConfig = ExtractionConfig(
            chunking=ChunkingConfig(
                max_chars=int(max_tokens * 0.9 * 4),
                max_overlap=int(max_tokens * 0.9 * 4 * 0.2),
            ),
            keywords=KeywordConfig(
                algorithm=KeywordAlgorithm.Rake,
                max_keywords=num_tags,
                min_score=0.5,  # Filter to top quality
                ngram_range=(1, 2),
                language="en",
            ),
        )

    async def tag_document(self, doc_path: str) -> list[str]:
        """Extract top N tags for a document."""
        result = await extract_file(doc_path, config=self.config)  # pyright: ignore[reportUnknownArgumentType]
        print(dir(result))  # pyright: ignore[reportUnknownArgumentType]
        print(result.metadata)  # pyright: ignore[reportUnknownArgumentType]
        keywords = result.metadata.get("keywords", [])

        # Return just the text, sorted by relevance
        sorted_keywords = sorted(keywords, key=lambda k: k.get("score", 0))  # pyright: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
        tags = [k.get("text", "") for k in sorted_keywords]

        return tags

    async def tag_batch(self, doc_paths: list[str]) -> dict[str, list[str]]:
        """Tag multiple documents."""
        results = {}
        for path in doc_paths:
            tags = await self.tag_document(path)
            results[path] = tags
        return results


# Usage
async def main():
    tagger = DocumentTagger(num_tags=5)

    # doc from args
    doc_path = sys.argv[1]
    print(f"Processing document: {doc_path}")
    documents = [doc_path]

    tags = await tagger.tag_batch(documents)

    for doc, doc_tags in tags.items():
        print(f"{doc}: {', '.join(doc_tags)}")


asyncio.run(main())
