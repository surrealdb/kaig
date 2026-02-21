<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { CircleAlert, CircleCheck, MoveRight, File, Folder } from '@lucide/svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import { RecordId } from 'surrealdb';

	type FileRecord = { id: RecordId; filename: string; path: string; is_folder: boolean };
	type FolderRecord = { id: RecordId; filename: string; path: string };

	let file = $state<FileRecord | null>(null);
	let folders = $state<FolderRecord[]>([]);
	let selectedFolderId = $state<string>('__root__');
	let loading = $state(true);
	let isMoving = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	let currentLocation = $derived(file?.path ? `/${file.path}` : '(root)');

	onMount(async () => {
		if (!$auth.isAuthenticated || !$auth.token || !page.params.file_id) {
			loading = false;
			return;
		}

		const token = $auth.token;
		try {
			const db = await getDb(token);
			try {
				const [fileResult, folderResult] = await Promise.all([
					db.query<[FileRecord[]]>(
						'SELECT id, filename, path, is_folder FROM file WHERE id = $id AND deleted_at = NONE LIMIT 1',
						{ id: new RecordId('file', page.params.file_id) }
					),
					db.query<[FolderRecord[]]>(
						'SELECT id, filename, path FROM file WHERE deleted_at = NONE AND is_folder = true ORDER BY path ASC'
					)
				]);
				file = fileResult[0][0] ?? null;
				folders = folderResult[0] ?? [];
			} finally {
				await db.close();
			}
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to load file';
		} finally {
			loading = false;
		}
	});

	async function moveFile(e: Event) {
		e.preventDefault();
		errorMessage = '';
		successMessage = '';

		if (!$auth.token || !file) return;
		if (!page.params.file_id) return;

		const token = $auth.token;
		const fileId = new RecordId('file', page.params.file_id);
		isMoving = true;
		try {
			const db = await getDb(token);
			try {
				if (selectedFolderId === '__root__') {
					await db.query('DELETE PARENT WHERE in = $id', { id: fileId });
				} else {
					const res = await db.query(
						'DELETE PARENT WHERE in = $id; RELATE $id->PARENT->$folder_id',
						{
							id: fileId,
							folder_id: new RecordId('file', selectedFolderId)
						}
					);
					console.log('res:', res, fileId, selectedFolderId);
				}
			} catch (err) {
				console.log(err);
			} finally {
				await db.close();
			}

			const db2 = await getDb(token);
			try {
				const refreshed = await db2.query<[FileRecord]>(
					'SELECT id, filename, path, is_folder FROM ONLY $record LIMIT 1',
					{ record: fileId }
				);
				file = refreshed[0] || file;
			} finally {
				await db2.close();
			}

			const targetLabel =
				selectedFolderId === '__root__'
					? 'root'
					: (folders.find((f) => String(f.id.id) === selectedFolderId)?.filename ??
						'selected folder');
			successMessage = `Moved to ${targetLabel}`;
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to move file';
		} finally {
			isMoving = false;
		}
	}
</script>

<div class="flex min-h-screen w-full flex-col items-center justify-center gap-4 px-4">
	<Card.Root class="mx-auto w-full max-w-md">
		<Card.Header>
			<Card.Title class="flex items-center gap-2 text-2xl">
				{#if loading}
					<Skeleton class="h-7 w-48" />
				{:else if file}
					{#if file.is_folder}
						<Folder size={20} />
					{:else}
						<File size={20} />
					{/if}
					{file.filename}
				{:else}
					File not found
				{/if}
			</Card.Title>
			<Card.Description>
				{#if loading}
					<Skeleton class="mt-1 h-4 w-64" />
				{:else if file}
					Current location: <span class="font-mono text-xs">{currentLocation}</span>
				{/if}
			</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if !$auth.isAuthenticated}
				<Alert.Root>
					<CircleAlert />
					<Alert.Title>Please log in to manage files.</Alert.Title>
				</Alert.Root>
			{:else if loading}
				<div class="flex flex-col gap-3">
					<Skeleton class="h-10 w-full" />
					<Skeleton class="h-10 w-full" />
				</div>
			{:else if !file}
				<Alert.Root variant="destructive">
					<CircleAlert />
					<Alert.Title>File not found or has been deleted.</Alert.Title>
				</Alert.Root>
			{:else}
				<form onsubmit={moveFile} class="flex flex-col gap-4">
					<div class="flex flex-col gap-1.5">
						<label for="folder-select" class="text-sm font-medium">Move to folder</label>
						<select
							id="folder-select"
							bind:value={selectedFolderId}
							disabled={isMoving}
							class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none disabled:opacity-50"
						>
							<option value="__root__">(root — no parent)</option>
							{#each folders as folder (folder.id)}
								{#if String(folder.id) !== String(file.id)}
									<option value={String(folder.id.id)}>
										{folder.path ? `/${folder.path}/${folder.filename}` : `/${folder.filename}`}
									</option>
								{/if}
							{/each}
						</select>
					</div>

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

					<Button type="submit" class="w-full" disabled={isMoving}>
						<MoveRight />
						{isMoving ? 'Moving...' : 'Move'}
					</Button>
				</form>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
