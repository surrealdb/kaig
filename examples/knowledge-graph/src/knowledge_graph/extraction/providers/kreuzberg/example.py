import asyncio

from kreuzberg import (
    ExtractionConfig,
    KeywordAlgorithm,
    KeywordConfig,
    extract_file,
)


class DocumentTagger:
    def __init__(self, num_tags: int = 5):
        self.config = ExtractionConfig(
            keywords=KeywordConfig(
                algorithm=KeywordAlgorithm.Yake,
                max_keywords=num_tags,
                min_score=0.3,  # Filter to top quality
                ngram_range=(1, 2),
                language="en",
            )
        )

    async def tag_document(self, doc_path: str) -> list[str]:
        """Extract top N tags for a document."""
        result = await extract_file(doc_path, config=self.config)
        print(dir(result))
        print(result.metadata)
        keywords = result.metadata.get("keywords", [])

        # Return just the text, sorted by relevance
        sorted_keywords = sorted(keywords, key=lambda k: k.score)
        tags = [k.text for k in sorted_keywords]

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

    documents = ["uploads/2026-01-29-knowledge-graph-rag.md"]

    tags = await tagger.tag_batch(documents)

    for doc, doc_tags in tags.items():
        print(f"{doc}: {', '.join(doc_tags)}")


asyncio.run(main())
