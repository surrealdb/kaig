import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import jwt from 'jsonwebtoken';
import { RecordId } from 'surrealdb';
import { getDb } from '$lib/server/db';
import { getConfig } from '$lib/server/config';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.pdf', '.md'];

export const POST: RequestHandler = async ({ request }) => {
	// Verify JWT
	const authHeader = request.headers.get('authorization');
	if (!authHeader?.startsWith('Bearer ')) {
		return new Response('unauthorized', { status: 401 });
	}

	const token = authHeader.slice(7);
	const config = getConfig();

	let claims: jwt.JwtPayload;
	try {
		claims = jwt.verify(token, config.jwtSecret, { algorithms: ['HS512'] }) as jwt.JwtPayload;
	} catch {
		return new Response('invalid token', { status: 401 });
	}

	const userIdStr = claims.id as string | undefined;
	if (!userIdStr) {
		return new Response('invalid token claims', { status: 401 });
	}

	// Parse "user:xyz" into a RecordId so SurrealDB accepts it as record<user>
	const parts = userIdStr.split(':');
	if (parts.length !== 2 || parts[0] !== 'user') {
		return new Response('invalid user id in token', { status: 401 });
	}
	const userId = new RecordId('user', parts[1]);

	// Parse form data
	let formData: FormData;
	try {
		formData = await request.formData();
	} catch {
		return new Response('invalid form data', { status: 400 });
	}

	const file = formData.get('file');
	if (!file || !(file instanceof File)) {
		return new Response('file is required', { status: 400 });
	}

	// Validate extension
	const filename = file.name;
	const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase();
	if (!ALLOWED_EXTENSIONS.includes(ext)) {
		return new Response(`only ${ALLOWED_EXTENSIONS.join(', ')} files are allowed`, { status: 400 });
	}

	// Validate size
	if (file.size > MAX_FILE_SIZE) {
		return new Response('file exceeds 10MB limit', { status: 400 });
	}

	// Read file bytes
	const arrayBuffer = await file.arrayBuffer();
	const bytes = new Uint8Array(arrayBuffer);

	// Insert into SurrealDB
	const db = await getDb();
	try {
		const [rows] = await db.query<[Record<string, unknown>[]]>(
			`CREATE file CONTENT $data RETURN AFTER`,
			{
				data: {
					owner: userId,
					filename,
					file: bytes
				}
			}
		);

		const created = rows[0];
		if (!created) {
			return new Response('failed to create file record', { status: 500 });
		}

		return json({ id: created.id, filename }, { status: 201 });
	} catch (err) {
		const msg = err instanceof Error ? err.message : String(err);
		return new Response(`failed to upload file: ${msg}`, { status: 500 });
	}
};
