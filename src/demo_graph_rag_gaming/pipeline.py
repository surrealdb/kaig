from .db import DB
from .embeddings import EmbeddingsGenerator


async def pipeline():
    db = DB()
    await db.open()
    embeddings_generator = EmbeddingsGenerator()
    try:
        await load_corpus(db, embeddings_generator)
        await query(db, embeddings_generator, "Tell me something about racing")
        await query(db, embeddings_generator, "Mistborn")
        await query(db, embeddings_generator, "Sports")
        await query(db, embeddings_generator, "Video games")
        await query(db, embeddings_generator, "Cooking recipe")
        await query(db, embeddings_generator, "Cars")
    except Exception as e:
        print(f"Error querying database: {e}")
        raise e
    finally:
        await db.close()


async def load_corpus(db: DB, embeddings_generator: EmbeddingsGenerator):
    print("Database opened")

    sentences = [
        "This is an example sentence",
        "Each sentence is converted",
        "This is really funny",
        "Jokes make people laugh",
        "Jokes are funny",
        "F1 teams are really competitive",
        "Racing drivers are athletes",
        "Driving a clown car",
        "Changing a motor's oil is a sport",
        "Baseball is played with a bat and a ball",
        "Allomancy is a magic system",
        "1 cup of chocolate",
    ]

    embeddings = embeddings_generator.generate_embeddings_list(sentences)
    # print(embeddings.shape)

    # similarities = model.similarity(embeddings, embeddings)
    # print(similarities)

    try:
        for i, embedding in enumerate(embeddings):
            await db.insert_embedding(embedding, sentences[i])
    except Exception as e:
        print(f"Error inserting embeddings: {e}")
        raise e


async def query(db: DB, embeddings_generator: EmbeddingsGenerator, text: str):
    print(f"Query: {text}")
    print("------------")
    res = await db.query(text, embeddings_generator)
    for result in res:
        print(f"{result['text']} ({result['dist']:.2f})")
    print()
