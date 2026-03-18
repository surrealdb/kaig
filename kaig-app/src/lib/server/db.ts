import { Surreal } from 'surrealdb';
import { getConfig } from './config.js';

let db: Surreal | null = null;

export async function getDb(): Promise<Surreal> {
	if (db) return db;

	const config = getConfig();
	const client = new Surreal();

	await client.connect(config.url);
	await client.signin({ username: config.username, password: config.password });
	await client.use({ namespace: config.namespace, database: config.database });

	db = client;
	return db;
}
