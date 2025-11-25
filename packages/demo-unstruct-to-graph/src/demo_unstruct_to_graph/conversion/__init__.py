from demo_unstruct_to_graph.conversion.providers import BaseConverter
from demo_unstruct_to_graph.conversion.providers.docling import DoclingConverter


class ConvertersFactory:
    @staticmethod
    def get_converter(content_type: str) -> BaseConverter:
        if DoclingConverter.supports_content_type(content_type):
            converter = DoclingConverter("text-embedding-3-large")
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
        return converter
