from langchain_community.vectorstores import SurrealDBStore
from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.text_splitter import SemanticChunker
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from surrealdb import AsyncSurreal, Surreal

from demo_langchain.surrealdb_graph import SurrealDBGraph

OLLAMA_MODEL = "llama3.2"

model = ChatOllama(model=OLLAMA_MODEL, temperature=0)


def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}


async def init_db(
    embeddings: Embeddings,
) -> tuple[SurrealDBStore, SurrealDBGraph]:
    async_conn = AsyncSurreal("ws://localhost:8000/rpc")
    await async_conn.signin({"username": "root", "password": "root"})
    await async_conn.use("langchain", "test")
    blocking_conn = Surreal("ws://localhost:8000/rpc")
    blocking_conn.signin({"username": "root", "password": "root"})
    blocking_conn.use("langchain", "test")
    vector_store = SurrealDBStore(embeddings, None, async_connection=async_conn)
    graph_store = SurrealDBGraph(blocking_conn)
    return vector_store, graph_store


def chat() -> dict:
    workflow = StateGraph(state_schema=MessagesState)
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = RunnableConfig({"configurable": {"thread_id": "abc123"}})
    messages = [
        SystemMessage(
            "Tell me about your company, and I'll give you a list of brand attributes that would fit it"
        ),
        HumanMessage(
            "Japanese snowboarding apparel and accessories online store"
        ),
        # HumanMessage(
        #     "SurrealDB is an end-to-end cloud-native database designed for modern applications, including web, mobile, serverless, Jamstack, backend, and traditional applications. With SurrealDB, you can simplify your database and API infrastructure, reduce development time, and build secure, performant apps quickly and cost-effectively."
        # ),
    ]
    output = app.invoke({"messages": messages}, config)
    return output


async def main():
    print("Hello from demo-langchain! Running...")
    embeddings = OllamaEmbeddings(model=OLLAMA_MODEL)
    vector_store, graph_store = await init_db(embeddings)

    output = chat()

    # Add LLM response to documents
    # But first let's split it semantically
    text_splitter = SemanticChunker(embeddings)
    documents = text_splitter.create_documents([output["messages"][-1].text()])

    # Generate graph
    llm_transformer = LLMGraphTransformer(
        llm=model,
        # allowed_nodes=["Brand", "Attribute"],
        # allowed_relationships=[
        #     ("Brand", "CHARACTERIZED_BY", "Attribute"),
        # ],
        # prompt="Extract attributes",
    )
    graph_documents = await llm_transformer.aconvert_to_graph_documents(
        documents
    )
    for graph_doc in graph_documents:
        print(f"Nodes:{graph_doc.nodes}")
        print(f"Relationships:{graph_doc.relationships}")

    # Store graph
    graph_store.add_graph_documents(graph_documents, include_source=True)
    print("Done with graph")

    # Store documents
    await vector_store.aadd_documents(documents)

    # Vector search
    results = await vector_store.asimilarity_search_with_relevance_scores(
        "visual attributes"
    )
    print("Results:")
    for result in results:
        print(result)
