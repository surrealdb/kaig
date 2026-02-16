import { RecordId } from 'surrealdb';

export type User = {
	id: RecordId;
	display_name: string;
	email: string;
};
