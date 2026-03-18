<script lang="ts">
	import { page } from '$app/state';
	import { CircleAlert, CircleCheck, Clock, MoveRight, File, Folder } from '@lucide/svelte';
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
	import { RecordId, Table } from 'surrealdb';
	import type { LiveSubscription, Surreal } from 'surrealdb';

	type FileRecord = {
		id: RecordId;
		filename: string;
		path: string;
		content_type: string;
		parent?: RecordId | null;
		flow_chunked?: string | null;
		flow_keywords?: string | null;
	};
	type FolderRecord = { id: RecordId; filename: string; path: string };

	let file = $state<FileRecord | null>(null);
	let folders = $state<FolderRecord[]>([]);
	let selectedFolderId = $state<string>('__root__');
	let loading = $state(true);
	let isMoving = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	let currentLocation = $derived(file?.path ? file.path : '(root)');

	let comboboxOpen = $state(false);
	let triggerRef = $state<HTMLButtonElement>(null!);

	const selectedFolderLabel = $derived(
		selectedFolderId === '__root__'
			? '(root — no parent)'
			: (() => {
					const f = folders.find((f) => String(f.id.id) === selectedFolderId);
					return f ? f.path : '';
				})()
	);

	function closeAndFocusTrigger() {
		comboboxOpen = false;
		tick().then(() => {
			triggerRef.focus();
		});
	}

	$effect(() => {
		const fileId = page.params.file_id;

		if (!$auth.isAuthenticated || !$auth.token || !fileId) {
			loading = false;
			return;
		}

		loading = true;
		errorMessage = '';
		successMessage = '';
		file = null;
		folders = [];

		const token = $auth.token;
		const recordId = new RecordId('file', fileId);

		let cancelled = false;
		let subscription: LiveSubscription | null = null;
		let db: Surreal | null = null;
		let unsubscribe: (() => void) | null = null;

		(async () => {
			try {
				db = await getDb(token);
				if (cancelled) {
					await db.close();
					return;
				}

				const [fileResult, folderResult] = await Promise.all([
					db.query<[FileRecord[]]>(
						'SELECT id, filename, path, content_type, parent, flow_chunked, flow_keywords FROM file WHERE id = $id AND deleted_at = NONE LIMIT 1',
						{ id: recordId }
					),
					db.query<[FolderRecord[]]>(
						"SELECT id, filename, path FROM file WHERE deleted_at = NONE AND content_type = 'folder' ORDER BY path ASC"
					)
				]);
				if (!cancelled) {
					file = fileResult[0][0] ?? null;
					folders = folderResult[0] ?? [];
					const parentId = file?.parent?.id;
					selectedFolderId = parentId ? String(parentId) : '__root__';
				}

				subscription = await db.live<FileRecord>(new Table('file'));
				if (cancelled) {
					await subscription.kill();
					await db.close();
					return;
				}

				unsubscribe = subscription.subscribe((message) => {
					if (message.action === 'UPDATE' && String(message.recordId) === String(recordId)) {
						file = message.value as FileRecord;
					}
				});
			} catch (err) {
				if (!cancelled) {
					errorMessage = err instanceof Error ? err.message : 'Failed to load file';
				}
			} finally {
				if (!cancelled) loading = false;
			}
		})();

		return () => {
			cancelled = true;
			loading = false;
			if (unsubscribe) unsubscribe();
			if (subscription) subscription.kill().catch(() => {});
			if (db) db.close().catch(() => {});
		};
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
					{#if file.content_type === 'folder'}
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
				<div class="mb-4 flex flex-col gap-2">
					<span class="text-sm font-medium">Processing status</span>
					{#snippet flowStatus(label: string, stamp: string | null | undefined)}
						<div class="flex items-center justify-between text-sm">
							<span class="text-muted-foreground">{label}</span>
							{#if stamp === 'failed'}
								<span class="flex items-center gap-1 text-destructive">
									<CircleAlert size={14} />
									Failed
								</span>
							{:else if stamp}
								<span class="flex items-center gap-1 text-green-600">
									<CircleCheck size={14} />
									Done
								</span>
							{:else}
								<span class="flex items-center gap-1 text-muted-foreground">
									<Clock size={14} />
									Pending
								</span>
							{/if}
						</div>
					{/snippet}
					{@render flowStatus('Chunked', file.flow_chunked)}
					{@render flowStatus('Keywords extracted', file.flow_keywords)}
				</div>
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
													{@const folderLabel = folder.path}
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
