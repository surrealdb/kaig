<script lang="ts">
	import { CircleAlert } from '@lucide/svelte';
	import { onMount } from 'svelte';

	import * as Card from '$lib/components/ui/card/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';

	import { fetchUser } from '$lib/api/user';
	import type { User } from '$lib/models/user';
	import { auth } from '$lib/stores/auth';

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

<Card.Root class="max-w-prose">
	{#if loading}
		<Card.Content>
			<Skeleton class="h-[125px] w-[250px] rounded-xl" />
		</Card.Content>
	{:else if !$auth.isAuthenticated}
		<Card.Content>
			<p>Please log in to view your profile.</p>
		</Card.Content>
	{:else if error}
		<Card.Content>
			<Alert.Root variant="destructive">
				<CircleAlert />
				<Alert.Title>{error}</Alert.Title>
			</Alert.Root>
		</Card.Content>
	{:else if user}
		<Card.Header>
			<Card.Title>{user.display_name}</Card.Title>
			<Card.Description>
				<div class="grid grid-cols-2 gap-4">
					<div>
						<dt>Display Name</dt>
						<dd>{user.display_name}</dd>
					</div>
					<div>
						<dt>Email</dt>
						<dd>{user.email}</dd>
					</div>
				</div>
			</Card.Description>
		</Card.Header>
	{/if}
</Card.Root>
