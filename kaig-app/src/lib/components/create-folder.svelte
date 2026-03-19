<script lang="ts">
	import { CircleAlert, CircleCheck, FolderPlus } from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import { RecordId, Table } from 'surrealdb';

	let folderName = $state('');
	let errorMessage = $state('');
	let successMessage = $state('');
	let isLoading = $state(false);

	async function createFolder(e: Event) {
		e.preventDefault();
		errorMessage = '';
		successMessage = '';

		if (!$auth.user) {
			errorMessage = 'You are not logged in';
			return;
		}

		const name = folderName.trim();
		if (!name) {
			errorMessage = 'Please enter a folder name';
			return;
		}

		const token = $auth.token;
		if (!token) {
			errorMessage = 'Not authenticated';
			return;
		}

		isLoading = true;
		try {
			const db = await getDb(token);
			await db.create(new Table('file')).content({
				owner: new RecordId(new Table('user'), $auth.user.id),
				filename: name,
				content_type: 'folder'
			});
			successMessage = `Folder "${name}" created`;
			folderName = '';
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to create folder';
		} finally {
			isLoading = false;
		}
	}
</script>

{#if !$auth.isAuthenticated}
	<Alert.Root>
		<CircleAlert />
		<Alert.Title>Please log in to create folders.</Alert.Title>
	</Alert.Root>
{:else}
	<form onsubmit={createFolder} class="flex flex-col gap-3">
		<Input type="text" placeholder="Folder name" bind:value={folderName} disabled={isLoading} />

		{#if errorMessage}
			<Alert.Root variant="destructive">
				<CircleAlert />
				<Alert.Title>{errorMessage}</Alert.Title>
			</Alert.Root>
		{/if}

		{#if successMessage}
			<Alert.Root>
				<CircleCheck />
				<Alert.Title>{successMessage}</Alert.Title>
			</Alert.Root>
		{/if}

		<Button type="submit" class="w-full" disabled={isLoading}>
			<FolderPlus />
			{isLoading ? 'Creating...' : 'Create Folder'}
		</Button>
	</form>
{/if}
