import { env } from '$env/dynamic/private';

export interface DbConfig {
	url: string;
	namespace: string;
	database: string;
	username: string;
	password: string;
	jwtSecret: string;
	jwtIssuer: string;
	jwtAudience: string;
}

function required(key: string): string {
	const value = env[key];
	if (!value) {
		throw new Error(`Environment variable ${key} is required`);
	}
	return value;
}

export function getConfig(): DbConfig {
	return {
		url: env.SURREALDB_URL ?? 'ws://localhost:8000',
		namespace: env.SURREALDB_NAMESPACE ?? 'test',
		database: env.SURREALDB_DATABASE ?? 'test',
		username: env.SURREALDB_USERNAME ?? 'root',
		password: env.SURREALDB_PASSWORD ?? 'root',
		jwtSecret: required('SURREALDB_JWT_SECRET'),
		jwtIssuer: required('SURREALDB_JWT_ISSUER'),
		jwtAudience: required('SURREALDB_JWT_AUDIENCE')
	};
}
