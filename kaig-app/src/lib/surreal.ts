import { Surreal } from 'surrealdb';
import { env } from '$env/dynamic/public';

let instance: { token: string; db: Surreal } | null = null;
let pending: Promise<Surreal> | null = null;

export async function getDb(token: string): Promise<Surreal> {
	if (instance?.token === token) return instance.db;
	if (pending) return pending;

	pending = (async () => {
		if (instance) {
			instance.db.close().catch(() => {});
			instance = null;
		}
		const db = new Surreal();
		await db.connect(env.PUBLIC_SURREALDB_URL ?? 'ws://localhost:8000');
		await db.use({
			namespace: env.PUBLIC_SURREALDB_NAMESPACE ?? 'test',
			database: env.PUBLIC_SURREALDB_DATABASE ?? 'test'
		});
		await db.authenticate(token);
		instance = { token, db };
		pending = null;
		return db;
	})();

	return pending;
}

export async function closeDb(): Promise<void> {
	pending = null;
	if (instance) {
		await instance.db.close().catch(() => {});
		instance = null;
	}
}
