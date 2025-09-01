use anyhow::Result;

pub async fn init_db() -> Result<()> {
    let query = include_str!("../surql/api.surql");
    let client = reqwest::Client::new();
    let _res = client
        .post("http://0.0.0.0:8000/sql")
        .header("Accept", "application/json")
        .header("Surreal-NS", "kaig-demo")
        .header("Surreal-DB", "main")
        .basic_auth("root", Some("root"))
        .body(query)
        .send()
        .await?;
    Ok(())
}

// use anyhow::{Context, Result};
// use surrealdb::Surreal;
// use surrealdb::engine::any::{self, Any};
// use surrealdb::opt::{
//     Config,
//     auth::Root,
//     capabilities::{Capabilities, ExperimentalFeature},
// };

// pub struct ConnConfig {
//     pub url: String,
//     pub username: String,
//     pub password: String,
//     pub namespace: String,
//     pub database: String,
// }

// impl ConnConfig {
//     pub fn default() -> Self {
//         Self {
//             url: "ws://0.0.0.0:8000".to_string(),
//             username: "root".to_string(),
//             password: "root".to_string(),
//             namespace: "test".to_string(),
//             database: "test".to_string(),
//         }
//     }
// }

// pub async fn connect(conn: &ConnConfig) -> Result<Surreal<Any>> {
//     let config = Config::default().capabilities(
//         Capabilities::default()
//             .allow_experimental_feature(ExperimentalFeature::DefineApi)
//             .to_owned(),
//     );
//     let client = any::connect((&conn.url, config))
//         .with_capacity(1000)
//         .await
//         .context("Failed to connect to SurrealDB")?;
//     client
//         .use_ns(&conn.namespace)
//         .use_db(&conn.database)
//         .await
//         .context("Failed to use namespace and database")?;

//     client
//         .signin(Root {
//             username: &conn.username,
//             password: &conn.password,
//         })
//         .await
//         .context("Failed to authenticate with SurrealDB")?;

//     Ok(client)
// }

// pub async fn init_db(db: &Surreal<Any>) -> Result<()> {
//     let query = include_str!("../surql/api.surql");
//     db.query(query).await?;
//     Ok(())
// }

// #[cfg(test)]
// mod tests {
//     use super::*;

//     fn test_config() -> ConnConfig {
//         ConnConfig {
//             url: "ws://localhost:8000".to_string(),
//             username: "root".to_string(),
//             password: "root".to_string(),
//             namespace: "test".to_string(),
//             database: "test".to_string(),
//         }
//     }

//     #[tokio::test]
//     #[ignore] // Ignored. Test with e2e test script
//     async fn test_database_connection() {
//         let config = test_config();
//         let db = connect(&config).await;
//         assert!(db.is_ok());
//     }
// }
