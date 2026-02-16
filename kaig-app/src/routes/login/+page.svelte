<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { auth } from '$lib/stores/auth';

	let mode = $state<'login' | 'signup'>('login');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		errorMessage = '';
		isLoading = true;

		try {
			const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/signup';
			const body =
				mode === 'signup'
					? { email, password, display_name: displayName || undefined }
					: { email, password };

			const res = await fetch(endpoint, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(body)
			});

			if (!res.ok) {
				const text = await res.text();
				errorMessage = text || `${mode === 'login' ? 'Login' : 'Signup'} failed`;
				return;
			}

			const data = await res.json();
			// Store the JWT token using the auth store
			auth.login(data.token, data.user);

			// Redirect to home page
			await goto(resolve('/'));
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	}

	function toggleMode() {
		mode = mode === 'login' ? 'signup' : 'login';
		errorMessage = '';
	}
</script>

<div class="flex min-h-screen items-center justify-center px-6 py-12">
	<div class="w-full max-w-md">
		<div class="rounded-2xl bg-slate-900 p-8 shadow-2xl ring-1 ring-slate-800">
			<h1 class="mb-2 text-center text-3xl font-bold tracking-tight">
				{mode === 'login' ? 'Welcome back' : 'Create account'}
			</h1>
			<p class="mb-8 text-center text-sm text-slate-400">
				{mode === 'login' ? 'Sign in to your account to continue' : 'Sign up to get started'}
			</p>

			<form onsubmit={handleSubmit} class="space-y-6">
				{#if mode === 'signup'}
					<div>
						<label for="displayName" class="mb-2 block text-sm font-medium text-slate-300">
							Display name (optional)
						</label>
						<input
							type="text"
							id="displayName"
							bind:value={displayName}
							class="w-full rounded-lg bg-slate-800 px-4 py-3 text-slate-50 placeholder-slate-400 ring-1 ring-slate-700 transition focus:ring-2 focus:ring-indigo-500 focus:outline-none"
							placeholder="Your name"
						/>
					</div>
				{/if}

				<div>
					<label for="email" class="mb-2 block text-sm font-medium text-slate-300"> Email </label>
					<input
						type="email"
						id="email"
						bind:value={email}
						required
						class="w-full rounded-lg bg-slate-800 px-4 py-3 text-slate-50 placeholder-slate-400 ring-1 ring-slate-700 transition focus:ring-2 focus:ring-indigo-500 focus:outline-none"
						placeholder="you@example.com"
					/>
				</div>

				<div>
					<label for="password" class="mb-2 block text-sm font-medium text-slate-300">
						Password
					</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						required
						minlength="8"
						class="w-full rounded-lg bg-slate-800 px-4 py-3 text-slate-50 placeholder-slate-400 ring-1 ring-slate-700 transition focus:ring-2 focus:ring-indigo-500 focus:outline-none"
						placeholder="••••••••"
					/>
				</div>

				{#if errorMessage}
					<div
						class="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-400 ring-1 ring-red-500/20"
					>
						{errorMessage}
					</div>
				{/if}

				<button
					type="submit"
					disabled={isLoading}
					class="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg ring-1 shadow-indigo-900/40 ring-indigo-400/60 transition hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{isLoading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Sign up'}
				</button>
			</form>

			<div class="mt-6 text-center">
				<button
					type="button"
					onclick={toggleMode}
					class="text-sm text-indigo-400 transition hover:text-indigo-300"
				>
					{mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
				</button>
			</div>
		</div>
	</div>
</div>
