<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { CircleAlert, CircleCheck, MoveRight, File, Folder } from '@lucide/svelte';
	import CheckIcon from '@lucide/svelte/icons/check';
	import ChevronsUpDownIcon from '@lucide/svelte/icons/chevrons-up-down';
	import { tick } from 'svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import { cn } from '$lib/utils.js';
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

	let comboboxOpen = $state(false);
	let triggerRef = $state<HTMLButtonElement>(null!);

	const selectedFolderLabel = $derived(
		selectedFolderId === '__root__'
			? '(root — no parent)'
			: (() => {
					const f = folders.find((f) => String(f.id.id) === selectedFolderId);
					return f ? (f.path ? `/${f.path}/${f.filename}` : `/${f.filename}`) : '';
				})()
	);

	function closeAndFocusTrigger() {
		comboboxOpen = false;
		tick().then(() => {
			triggerRef.focus();
		});
	}

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
				const res = await db.update(fileId).merge({
					parent: selectedFolderId === '__root__' ? null : new RecordId('file', selectedFolderId)
				});
				console.log('res:', res, fileId, selectedFolderId);

				const refreshed = await db.query<[FileRecord]>(
					'SELECT id, filename, path, is_folder FROM ONLY $record LIMIT 1',
					{ record: fileId }
				);
				file = refreshed[0] || file;
			} catch (err) {
				console.log(err);
			} finally {
				await db.close();
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
						<span class="text-sm font-medium">Move to folder</span>
						<Popover.Root bind:open={comboboxOpen}>
							<Popover.Trigger bind:ref={triggerRef}>
								{#snippet child({ props })}
									<Button
										variant="outline"
										class="w-full justify-between"
										{...props}
										role="combobox"
										aria-expanded={comboboxOpen}
										disabled={isMoving}
									>
										{selectedFolderLabel || 'Select a folder...'}
										<ChevronsUpDownIcon class="ms-2 size-4 shrink-0 opacity-50" />
									</Button>
								{/snippet}
							</Popover.Trigger>
							<Popover.Content class="w-full p-0">
								<Command.Root>
									<Command.Input placeholder="Search folder..." />
									<Command.List>
										<Command.Empty>No folder found.</Command.Empty>
										<Command.Group>
											<Command.Item
												value="__root__"
												onSelect={() => {
													selectedFolderId = '__root__';
													closeAndFocusTrigger();
												}}
											>
												<CheckIcon
													class={cn(
														'me-2 size-4',
														selectedFolderId !== '__root__' && 'text-transparent'
													)}
												/>
												(root — no parent)
											</Command.Item>
											{#each folders as folder (folder.id)}
												{#if String(folder.id) !== String(file.id)}
													{@const folderId = String(folder.id.id)}
													{@const folderLabel = folder.path
														? `/${folder.path}/${folder.filename}`
														: `/${folder.filename}`}
													<Command.Item
														value={folderId}
														onSelect={() => {
															selectedFolderId = folderId;
															closeAndFocusTrigger();
														}}
													>
														<CheckIcon
															class={cn(
																'me-2 size-4',
																selectedFolderId !== folderId && 'text-transparent'
															)}
														/>
														{folderLabel}
													</Command.Item>
												{/if}
											{/each}
										</Command.Group>
									</Command.List>
								</Command.Root>
							</Popover.Content>
						</Popover.Root>
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
