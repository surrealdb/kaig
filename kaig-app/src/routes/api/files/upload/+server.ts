import { createHash } from 'crypto';
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import jwt from 'jsonwebtoken';
import { RecordId } from 'surrealdb';
import { getDb } from '$lib/server/db';
import { getConfig } from '$lib/server/config';

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ALLOWED_EXTENSIONS = ['.pdf', '.md', '.mdx', '.mdc'];
const TEXT_EXTENSIONS = new Set(['.md', '.mdx', '.mdc']);
const CONTENT_TYPES: Record<string, string> = {
	'.pdf': 'application/pdf',
	'.md': 'text/markdown',
	'.mdx': 'text/mdx',
	'.mdc': 'text/plain'
};

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
		return new Response('file exceeds 20MB limit', { status: 400 });
	}

	const content_type = CONTENT_TYPES[ext] ?? file.type;
	const arrayBuffer = await file.arrayBuffer();

	// const hash = createHash('sha256').update(Buffer.from(arrayBuffer)).digest('hex');
	const hash = createHash('md5').update(Buffer.from(arrayBuffer)).digest('hex');
	const fileId = new RecordId('file', hash);

	const data = TEXT_EXTENSIONS.has(ext)
		? {
				id: fileId,
				owner: userId,
				content_type,
				filename,
				content: new TextDecoder().decode(arrayBuffer)
			}
		: { id: fileId, owner: userId, content_type, filename, file: new Uint8Array(arrayBuffer) };

	// Insert into SurrealDB (idempotent: same content hash → same ID, duplicate is ignored)
	const db = await getDb();
	try {
		await db.query(`INSERT IGNORE INTO file $data RETURN NONE`, { data });
		return json({ id: fileId, filename }, { status: 201 });
	} catch (err) {
		const msg = err instanceof Error ? err.message : String(err);
		return new Response(`failed to upload file: ${msg}`, { status: 500 });
	}
};
