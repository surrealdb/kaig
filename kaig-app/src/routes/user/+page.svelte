<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/stores/auth';
	import { fetchUser } from '$lib/api/user';
	import type { User } from '$lib/models/user';

	let user: User | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

	onMount(async () => {
		if (!$auth.isAuthenticated || !$auth.token || !$auth.user?.id) {
			loading = false;
			return;
		}

		try {
			const userId = String($auth.user.id);
			user = await fetchUser($auth.token, userId);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load user';
		} finally {
			loading = false;
		}
	});
</script>

<div class="mx-auto max-w-2xl px-6 pt-24">
	{#if loading}
		<p class="text-slate-400">Loading...</p>
	{:else if !$auth.isAuthenticated}
		<p class="text-slate-400">Please log in to view your profile.</p>
	{:else if error}
		<p class="text-red-400">{error}</p>
	{:else if user}
		<h1 class="mb-6 text-2xl font-semibold text-slate-50">{user.display_name}</h1>
		<div class="rounded-xl border border-slate-800 bg-slate-900 p-6">
			<dl class="space-y-4">
				<div>
					<dt class="text-sm text-slate-400">Display Name</dt>
					<dd class="text-slate-50">{user.display_name}</dd>
				</div>
				<div>
					<dt class="text-sm text-slate-400">Email</dt>
					<dd class="text-slate-50">{user.email}</dd>
				</div>
			</dl>
		</div>
	{/if}
</div>
