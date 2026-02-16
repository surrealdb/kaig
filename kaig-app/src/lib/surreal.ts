import { Surreal } from 'surrealdb';
import { env } from '$env/dynamic/public';

export async function getDb(token: string): Promise<Surreal> {
	const db = new Surreal();

	await db.connect(env.PUBLIC_SURREALDB_URL ?? 'ws://localhost:8000');
	await db.use({
		namespace: env.PUBLIC_SURREALDB_NAMESPACE ?? 'test',
		database: env.PUBLIC_SURREALDB_DATABASE ?? 'test'
	});
	await db.authenticate(token);

	return db;
}
