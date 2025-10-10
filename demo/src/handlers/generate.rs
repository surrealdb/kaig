use std::collections::HashMap;

use actix_web::{Responder, error::ErrorInternalServerError, post, web};
use new_string_template::template::Template;
use ollama_rs::generation::{completion::request::GenerationRequest, parameters::KeepAlive};
use serde::Deserialize;

use crate::state::AppState;

#[derive(Deserialize, Debug)]
struct GenerateParams {
    sys_prompt: String,
    usr_prompt: String,
    context: String,
}

#[post("/generate")]
pub async fn generate(
    input: web::Json<GenerateParams>,
    data: web::Data<AppState>,
) -> impl Responder {
    #[cfg(debug_assertions)]
    tracing::debug!("/generate with {:?}", input);

    let templ = Template::new(&input.sys_prompt);
    let prompt_vars = HashMap::from([
        ("prompt", input.usr_prompt.clone()),
        ("context", input.context.clone()),
    ]);
    let rendered = templ.render_nofail(&prompt_vars);

    let res = data
        .ollama
        .generate(
            // TODO: review options
            GenerationRequest::new(data.llm_model_name.clone(), rendered)
                .keep_alive(KeepAlive::Indefinitely),
        )
        .await;
    match res {
        Ok(res) => Ok(res.response),
        Err(e) => Err(ErrorInternalServerError(e)),
    }
}
