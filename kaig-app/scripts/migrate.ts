import { Surreal } from 'surrealdb';
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

const url = process.env.SURREALDB_URL ?? 'ws://localhost:8000';
const namespace = process.env.SURREALDB_NAMESPACE ?? 'test';
const database = process.env.SURREALDB_DATABASE ?? 'test';
const username = process.env.SURREALDB_USERNAME ?? 'root';
const password = process.env.SURREALDB_PASSWORD ?? 'root';

async function main() {
	const db = new Surreal();
	await db.connect(url);
	await db.signin({ username, password });
	await db.use({ namespace, database });

	const migrationsDir = join(import.meta.dirname, '..', 'migrations');
	const files = (await readdir(migrationsDir)).filter((f) => f.endsWith('.surql')).sort();

	for (const file of files) {
		const sql = await readFile(join(migrationsDir, file), 'utf-8');
		console.log(`Running ${file}...`);
		try {
			await db.query(sql);
			console.log(`  OK`);
		} catch (err) {
			console.error(`  FAILED: ${err}`);
			process.exit(1);
		}
	}

	await db.close();
	console.log('All migrations complete.');
}

main();
