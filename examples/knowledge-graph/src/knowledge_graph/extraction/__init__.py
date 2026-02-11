import logging

from .providers import BaseConverter
from .providers.docling import DoclingConverter
from .providers.kreuzberg.kreuzberg_converter import (
    KreuzbergConverter,
)

logger = logging.getLogger(__name__)


class ConvertersFactory:
    @staticmethod
    def get_converter(content_type: str, embedding_model: str) -> BaseConverter:
        if KreuzbergConverter.supports_content_type(content_type):
            converter = KreuzbergConverter(content_type)
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
