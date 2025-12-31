import logging

from demo_unstruct_to_graph.conversion.providers import BaseConverter
from demo_unstruct_to_graph.conversion.providers.docling import DoclingConverter
from demo_unstruct_to_graph.conversion.providers.kreuzberg import (
    KreuzbergConverter,
)

logger = logging.getLogger(__name__)


class ConvertersFactory:
    @staticmethod
    def get_converter(content_type: str, embedding_model: str) -> BaseConverter:
        if KreuzbergConverter.supports_content_type(content_type):
            converter = KreuzbergConverter(embedding_model, content_type)
            logger.info(
                f"Using KreuzbergConverter for content type {content_type}"
            )
        elif DoclingConverter.supports_content_type(content_type):
            converter = DoclingConverter(embedding_model)
            logger.info(
                f"Using DoclingConverter for content type {content_type}"
            )
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
        return converter
