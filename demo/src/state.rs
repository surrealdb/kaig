use ollama_rs::Ollama;

pub struct AppState {
    pub ollama: Ollama,
    pub embedding_model_name: String,
    pub llm_model_name: String,
}
