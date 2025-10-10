use actix_cors::Cors;
use actix_web::{App, HttpServer, middleware::Logger, web};
use clap::Parser;
use ollama_rs::Ollama;
use tracing::level_filters::LevelFilter;
use tracing_subscriber::EnvFilter;

use crate::state::AppState;

mod handlers;
mod state;

/// Embeddings generator micro service
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct Args {
    /// Embeddings model
    #[arg(short, long)]
    embeddings_model: String,

    /// LLM model
    #[arg(short, long)]
    llm_model: String,

    /// Host
    #[arg(long, default_value = "127.0.0.1")]
    host: String,

    /// Port
    #[arg(short, long, default_value_t = 8080)]
    port: u16,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt()
        .with_ansi(true)
        .with_env_filter(
            EnvFilter::builder()
                .with_default_directive(LevelFilter::DEBUG.into())
                .from_env_lossy(),
        )
        .init();

    let ollama = Ollama::default();
    // let ollama = Ollama::new("http://localhost".to_string(), 11434);

    let args = Args::parse();
    tracing::info!("Starting server with {:?}", args);
    let app_state = web::Data::new(AppState {
        ollama,
        embedding_model_name: args.embeddings_model,
        llm_model_name: args.llm_model,
    });

    HttpServer::new(move || {
        let cors = Cors::default()
            .allowed_origin("https://app.surrealdb.com")
            .allowed_origin_fn(|origin, _req_head| {
                origin.as_bytes().starts_with(b"http://localhost")
            })
            .allow_any_header()
            .allowed_methods(vec!["GET", "POST", "HEAD"]);
        App::new()
            .wrap(cors)
            .wrap(Logger::default())
            .app_data(app_state.clone())
            .service(handlers::hello)
            .service(handlers::embed::embed)
            .service(handlers::generate::generate)
    })
    .bind((args.host, args.port))?
    .run()
    .await
}
