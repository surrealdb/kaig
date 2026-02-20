<script lang="ts">
	import { CircleAlert, CircleCheck, FolderPlus } from '@lucide/svelte';
	import UploadForm from '$lib/components/upload-form.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
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
				filename: name,
				owner: new RecordId(new Table('user'), $auth.user.id)
			});
			await db.close();
			successMessage = `Folder "${name}" created`;
			folderName = '';
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to create folder';
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="flex min-h-screen w-full flex-col items-center justify-center gap-4 px-4">
	<UploadForm />

	<Card.Root class="mx-auto w-full max-w-sm">
		<Card.Header>
			<Card.Title class="text-2xl">New Folder</Card.Title>
			<Card.Description>Create a new folder</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if !$auth.isAuthenticated}
				<Alert.Root>
					<CircleAlert />
					<Alert.Title>Please log in to create folders.</Alert.Title>
				</Alert.Root>
			{:else}
				<form onsubmit={createFolder} class="flex flex-col gap-3">
					<Input
						type="text"
						placeholder="Folder name"
						bind:value={folderName}
						disabled={isLoading}
					/>

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
		</Card.Content>
	</Card.Root>
</div>
