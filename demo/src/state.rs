use ollama_rs::Ollama;

pub struct AppState {
    pub ollama: Ollama,
    pub model_name: String,
}
