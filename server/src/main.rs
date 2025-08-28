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
    /// Ollama model
    #[arg(short, long)]
    ollama_model: String,

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
                .with_default_directive(LevelFilter::INFO.into())
                .from_env_lossy(),
        )
        .init();

    let ollama = Ollama::default();
    // let ollama = Ollama::new("http://localhost".to_string(), 11434);

    let args = Args::parse();
    tracing::info!("Starting server with {:?}", args);
    // let config = Env::load()?;
    let app_state = web::Data::new(AppState {
        ollama,
        model_name: args.ollama_model,
    });

    HttpServer::new(move || {
        App::new()
            .wrap(Logger::default())
            .app_data(app_state.clone())
            .service(handlers::hello)
            .service(handlers::embed)
    })
    .bind((args.host, args.port))?
    .run()
    .await
}
