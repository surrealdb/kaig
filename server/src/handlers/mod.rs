use actix_web::{HttpResponse, Responder, error::ErrorInternalServerError, get, post, web};
use ollama_rs::generation::{
    embeddings::request::{EmbeddingsInput, GenerateEmbeddingsRequest},
    parameters::KeepAlive,
};

use crate::state::AppState;

#[get("/")]
pub async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Hello world!")
}

#[post("/embed")]
pub async fn embed(req_body: String, data: web::Data<AppState>) -> impl Responder {
    let input = req_body;
    #[cfg(debug_assertions)]
    tracing::debug!("Embedding input: {}", input);
    let res = data
        .ollama
        .generate_embeddings(
            GenerateEmbeddingsRequest::new(data.model_name.clone(), EmbeddingsInput::Single(input))
                .keep_alive(KeepAlive::Indefinitely),
        )
        .await;
    match res {
        Ok(res) => match res.embeddings.into_iter().next().map(|x| web::Json(x)) {
            Some(x) => Ok(x),
            None => Err(ErrorInternalServerError("unexpected ollama response")),
        },
        Err(e) => Err(ErrorInternalServerError(e)),
    }
}
