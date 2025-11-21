import logging
from pathlib import Path
from typing import override

import tiktoken
from docling.datamodel.base_models import InputFormat
from docling.document_converter import (
    DocumentConverter,
    FormatOption,
    PdfFormatOption,
)
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer
from docling_core.types.doc.document import DoclingDocument
from docling_core.types.io import DocumentStream

from demo_unstruct_to_graph.conversion.definitions import ChunkDocumentResult

logger = logging.getLogger(__name__)

TMP_CHUNK_DIR = Path("tmp/chunks")
TMP_CHUNK_DIR.mkdir(exist_ok=True, parents=True)


def _count_tokens(text: str, tokenizer: OpenAITokenizer) -> int:
    return len(tokenizer.get_tokenizer().encode(text))


def _merge_short_chunks(
    chunks: list[str],
    tokenizer: OpenAITokenizer,
    min_tokens: int = 40,
    max_tokens: int = 256,
) -> list[str]:
    """Merge chunks that are below min_tokens with their neighbors.

    Args:
        chunks: List of text chunks to process
        tokenizer: Tokenizer for counting tokens
        min_tokens: Minimum token count threshold
        max_tokens: Maximum token count after merging

    Returns:
        List of merged chunks
    """
    if not chunks:
        return chunks

    # Track which chunks have been merged
    merged_indices: set[int] = set()
    result: list[str] = []

    i = 0
    while i < len(chunks):
        # Skip if already merged
        if i in merged_indices:
            i += 1
            continue

        current_chunk = chunks[i]
        current_tokens = _count_tokens(current_chunk, tokenizer)

        # If chunk is large enough, keep it as-is
        if current_tokens >= min_tokens:
            result.append(current_chunk)
            i += 1
            continue

        # Chunk is too short, try to merge
        merged = False

        # Case 1: First chunk (too short) - merge with next if possible
        if i == 0 and i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            combined = current_chunk + "\n\n" + next_chunk
            combined_tokens = _count_tokens(combined, tokenizer)

            if combined_tokens <= max_tokens:
                result.append(combined)
                merged_indices.add(i + 1)
                merged = True

        # Case 2: Last chunk (too short) - merge with previous if possible
        elif i == len(chunks) - 1 and len(result) > 0:
            # Merge with the last item in result (previous chunk)
            prev_chunk = result[-1]
            combined = prev_chunk + "\n\n" + current_chunk
            combined_tokens = _count_tokens(combined, tokenizer)

            if combined_tokens <= max_tokens:
                result[-1] = combined
                merged = True

        # Case 3: Middle chunk (too short) - merge with smaller neighbor
        elif 0 < i < len(chunks) - 1:
            prev_chunk = chunks[i - 1] if i - 1 not in merged_indices else None
            next_chunk = chunks[i + 1]

            # Determine which neighbor to try first (smaller one)
            if prev_chunk is not None:
                prev_tokens = _count_tokens(prev_chunk, tokenizer)
                next_tokens = _count_tokens(next_chunk, tokenizer)
                try_prev_first = prev_tokens <= next_tokens
            else:
                try_prev_first = False

            if try_prev_first and prev_chunk is not None:
                # Try merging with previous
                combined = result[-1] + "\n\n" + current_chunk
                combined_tokens = _count_tokens(combined, tokenizer)

                if combined_tokens <= max_tokens:
                    result[-1] = combined
                    merged = True
                else:
                    # Try merging with next instead
                    combined = current_chunk + "\n\n" + next_chunk
                    combined_tokens = _count_tokens(combined, tokenizer)

                    if combined_tokens <= max_tokens:
                        result.append(combined)
                        merged_indices.add(i + 1)
                        merged = True
            else:
                # Try merging with next first
                combined = current_chunk + "\n\n" + next_chunk
                combined_tokens = _count_tokens(combined, tokenizer)

                if combined_tokens <= max_tokens:
                    result.append(combined)
                    merged_indices.add(i + 1)
                    merged = True
                elif prev_chunk is not None:
                    # Try merging with previous instead
                    combined = result[-1] + "\n\n" + current_chunk
                    combined_tokens = _count_tokens(combined, tokenizer)

                    if combined_tokens <= max_tokens:
                        result[-1] = combined
                        merged = True

        # If merge failed, keep chunk as-is (even if too short)
        if not merged:
            result.append(current_chunk)

        i += 1

    return result


class MarkdownSerializerProvider(ChunkingSerializerProvider):
    @override
    def get_serializer(self, doc: DoclingDocument):
        return MarkdownDocSerializer(doc=doc)


def chunk(doc: DoclingDocument, tokenizer: OpenAITokenizer) -> list[str]:
    chunker = HybridChunker(
        serializer_provider=MarkdownSerializerProvider(),
        tokenizer=tokenizer,
    )
    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks: list[str] = []
    for chunk in chunk_iter:
        enriched_text = chunker.contextualize(chunk=chunk)
        chunks.append(enriched_text)
    return chunks


def convert_and_chunk(
    source: Path | DocumentStream,
    format: InputFormat,
    option: FormatOption,
    model_name: str,
) -> ChunkDocumentResult:
    """Converts and chunks a PDF document"""
    # context window length required for OpenAI tokenizers
    max_tokens = 128 * 1024

    tokenizer = OpenAITokenizer(
        tokenizer=tiktoken.encoding_for_model(model_name),
        max_tokens=max_tokens,
    )

    converter = DocumentConverter(
        allowed_formats=[format],
        format_options={format: option},
    )
    result = converter.convert(source)

    try:
        chunks = chunk(result.document, tokenizer)
    except Exception as e:
        logger.error(f"Error chunking doc {source.name}: {e}")
        raise e

    # Post-process: merge too-short chunks with neighbours
    chunks = _merge_short_chunks(chunks, tokenizer, 60, max_tokens)

    for i, c in enumerate(chunks):
        with open(TMP_CHUNK_DIR / f"out_chunk_{source.name}_{i}.md", "w") as f:
            _ = f.write(c)

    return ChunkDocumentResult(filename=source.name, chunks=chunks)


if __name__ == "__main__":
    import sys

    file = sys.argv[1]

    source = Path(file)
    result = convert_and_chunk(
        source, InputFormat.PDF, PdfFormatOption(), "gpt-4o"
    )
    print(result)
    print("-------------------------------------------------------------------")
    for j, x in enumerate(result.chunks):
        print(f"  - {j}: {len(x)}")
