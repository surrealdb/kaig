# Embedding Models 101

How are we going to create the embeddings?

**Different models**:

- GloVe: word based, easier-faster (300 dimensions) ? tokens -> small datasets
- BERT: contextual, more accurate (768 dimensions) 512 tokens -> semantic-rich text (descriptions,reviews)
- RoBERTA: contextual, even more accurate (1024 dimensions) -> complex semantics, high accuracy
- SBERT: sentence context, more efficient but less contextual depth (? dimensions) ? tokens -> balanced speed/accuracy (product titles)
- Longformer: transformer-based, 4,096 tokens -> long product descriptions
- BGE: sentence context (? dimensions) ? tokens -> high-precision semantic search
- DistilBERT: word based, lightweight (? dimensions) ? tokens -> low resource
- MiniLM: (? dimensions) ? tokens -> low resource

**To decide we need to understand our data and think about:**

- efficiency (cost) vs. accuracy
- using different models for different data
- experimenting with different alternatives is definitely a good option, will that be part of the early stages, or after you have an initial POC?
- do we need to aggregate our data with more data?

## Steps

1. pre-processing (cleaning, chunking)
2. generate embeddings
3. benchmark models
4. benckmark vector index parameters
