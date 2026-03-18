import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { signupUser, AuthError } from '$lib/server/auth';

export const POST: RequestHandler = async ({ request }) => {
	let body: { email?: string; password?: string; display_name?: string };
	try {
		body = await request.json();
	} catch {
		return new Response('invalid JSON', { status: 400 });
	}

	const { email, password, display_name } = body;
	if (!email || !password) {
		return new Response('email and password are required', { status: 400 });
	}

	try {
		const result = await signupUser(email, password, display_name);
		return json(result, { status: 201 });
	} catch (err) {
		if (err instanceof AuthError) {
			return new Response(err.message, { status: err.status });
		}
		return new Response('internal server error', { status: 500 });
	}
};
