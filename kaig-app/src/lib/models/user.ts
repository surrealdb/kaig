import type { RecordId } from 'surrealdb';

export type User = {
	id: RecordId<string, string>;
	display_name: string;
	email: string;
};
