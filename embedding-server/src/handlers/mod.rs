use actix_web::{HttpResponse, Responder, get};

pub mod embed;
pub mod generate;

#[get("/")]
pub async fn hello() -> impl Responder {
    HttpResponse::Ok().body("Hello world!")
}
