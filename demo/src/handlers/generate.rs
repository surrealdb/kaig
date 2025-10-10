use std::collections::HashMap;

use actix_web::{Responder, error::ErrorInternalServerError, post, web};
use new_string_template::template::Template;
use ollama_rs::{
    generation::{completion::request::GenerationRequest, parameters::KeepAlive},
    models::ModelOptions,
};
use serde::Deserialize;
use serde_json::Value;

use crate::state::AppState;

#[derive(Deserialize, Debug)]
struct GenerateParams {
    system: String,
    prompt: String,
    vars: Value,
}

#[post("/generate")]
pub async fn generate(
    input: web::Json<GenerateParams>,
    data: web::Data<AppState>,
) -> impl Responder {
    #[cfg(debug_assertions)]
    tracing::debug!("/generate with {:?}", input);

    let templ = Template::new(&input.prompt);
    let prompt_vars: HashMap<String, String> =
        serde_json::from_value(input.vars.clone()).unwrap_or_default();
    // let prompt_vars: HashMap<String, Value> =
    //     serde_json::from_value(input.vars.clone()).unwrap_or_default();
    let prompt_vars: HashMap<&str, String> = prompt_vars
        .iter()
        .map(|(k, v)| (k.as_str(), v.clone()))
        .collect();
    let rendered = templ.render_nofail(&prompt_vars);

    #[cfg(debug_assertions)]
    tracing::debug!("Rendered prompt: {}", rendered);

    let res = data
        .ollama
        .generate(
            // options reference: https://docs.ollama.com/modelfile
            GenerationRequest::new(data.llm_model_name.clone(), rendered)
                .options(ModelOptions::default().temperature(0.8))
                .system(input.system.clone())
                .keep_alive(KeepAlive::Indefinitely),
        )
        .await;
    match res {
        Ok(res) => Ok(res.response),
        Err(e) => Err(ErrorInternalServerError(e)),
    }
}
