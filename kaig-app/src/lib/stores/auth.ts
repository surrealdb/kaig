import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from '$lib/models/user';

export type AuthState = {
	token: string | null;
	user: User | null;
	isAuthenticated: boolean;
};

function createAuthStore() {
	const initialState: AuthState = {
		token: null,
		user: null,
		isAuthenticated: false
	};

	// Load from localStorage if in browser
	if (browser) {
		const token = localStorage.getItem('auth_token');
		const userJson = localStorage.getItem('user');
		if (token && userJson) {
			try {
				const user = JSON.parse(userJson);
				initialState.token = token;
				initialState.user = user;
				initialState.isAuthenticated = true;
			} catch (err) {
				console.error('Failed to parse stored user', err);
			}
		}
	}

	const { subscribe, set } = writable<AuthState>(initialState);

	return {
		subscribe,
		login: (token: string, user: User) => {
			if (browser) {
				localStorage.setItem('auth_token', token);
				localStorage.setItem('user', JSON.stringify(user));
			}
			set({ token, user, isAuthenticated: true });
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('auth_token');
				localStorage.removeItem('user');
			}
			set({ token: null, user: null, isAuthenticated: false });
		},
		set
	};
}

export const auth = createAuthStore();

// Helper function to get authorization header
export function getAuthHeader(): Record<string, string> {
	if (browser) {
		const token = localStorage.getItem('auth_token');
		if (token) {
			return { Authorization: `Bearer ${token}` };
		}
	}
	return {};
}
