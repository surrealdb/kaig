# from demo_unstruct_to_graph.conversion.pdf import convert_and_chunk
from demo_unstruct_to_graph.db import init_db


def main() -> None:
    import sys

    file = sys.argv[1]

    db = init_db(True)

    doc, cached = db.store_original_document(file)

    # --------------------------------------------------------------------------
    # Convert and chunk
    # result = convert_and_chunk(source)
