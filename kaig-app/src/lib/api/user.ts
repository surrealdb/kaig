import { RecordId } from 'surrealdb';
import { getDb } from '$lib/surreal';
import type { User } from '$lib/models/user';

export const fetchUser = async (token: string, user_id: string): Promise<User> => {
	const db = await getDb(token);
	const user = await db.select<User>(new RecordId('user', user_id));
	if (!user) throw new Error('User not found');
	return user;
};
