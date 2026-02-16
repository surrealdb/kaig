import * as argon2 from 'argon2';
import jwt from 'jsonwebtoken';
import { getDb } from './db.js';
import { getConfig, type DbConfig } from './config.js';

export interface BasicUser {
	id: string;
	email: string;
	display_name: string | null;
}

export interface AuthResult {
	token: string;
	user: BasicUser;
}

interface StoredUser {
	id: { tb: string; id: string };
	email: string;
	display_name: string | null;
	password_hash: string;
	role: string;
}

function getStringId(recordId: { tb: string; id: string }): string {
	return String(recordId.id);
}

async function hashPassword(password: string): Promise<string> {
	return argon2.hash(password);
}

function issueToken(userId: string, role: string | null, config: DbConfig): string {
	const now = Math.floor(Date.now() / 1000);
	const claims: Record<string, unknown> = {
		exp: now + 24 * 60 * 60,
		iat: now,
		iss: config.jwtIssuer,
		aud: config.jwtAudience,
		ns: config.namespace,
		db: config.database,
		id: `user:${userId}`,
		ac: 'record_access'
	};
	if (role) {
		claims.role = role;
	}
	return jwt.sign(claims, config.jwtSecret, { algorithm: 'HS512' });
}

export async function signupUser(
	email: string,
	password: string,
	displayName?: string
): Promise<AuthResult> {
	const db = await getDb();
	const config = getConfig();

	const emailNormalized = email.toLowerCase();
	const passwordHash = await hashPassword(password);

	let rows: StoredUser[];
	try {
		[rows] = await db.query<[StoredUser[]]>('CREATE user CONTENT $data RETURN AFTER', {
			data: {
				email: emailNormalized,
				password_hash: passwordHash,
				display_name: displayName ?? null,
				role: 'user'
			}
		});
	} catch (err: unknown) {
		const msg = err instanceof Error ? err.message : String(err);
		if (msg.includes('idx_user_email_unique')) {
			throw new AuthError('email already registered', 400);
		}
		throw new AuthError(`Failed to create user: ${msg}`, 400);
	}

	const created = rows[0];
	if (!created) {
		throw new AuthError('user not created', 400);
	}

	const userId = getStringId(created.id);
	const token = issueToken(userId, created.role, config);

	return {
		token,
		user: {
			id: userId,
			email: created.email,
			display_name: created.display_name
		}
	};
}

export async function signinUser(email: string, password: string): Promise<AuthResult> {
	const db = await getDb();
	const config = getConfig();

	const [rows] = await db.query<[StoredUser[]]>(
		`SELECT id, email, display_name, password_hash, role
		 FROM user
		 WHERE email = string::lowercase($email)
		 AND crypto::argon2::compare(password_hash, $password)
		 LIMIT 1`,
		{ email, password }
	);

	const user = rows[0];
	if (!user) {
		throw new AuthError('user not found', 401);
	}

	const userId = getStringId(user.id);
	const token = issueToken(userId, user.role, config);

	return {
		token,
		user: {
			id: userId,
			email: user.email,
			display_name: user.display_name
		}
	};
}

export class AuthError extends Error {
	status: number;

	constructor(message: string, status: number) {
		super(message);
		this.name = 'AuthError';
		this.status = status;
	}
}
