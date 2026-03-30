<script lang="ts">
	import { page } from '$app/state';
	import MoveFile from '@/components/move-file.svelte';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import { RecordId } from 'surrealdb';
	import * as Accordion from '$lib/components/ui/accordion';
	import * as Card from '$lib/components/ui/card/index.js';

	type FileRecord = {
		id: unknown;
		filename: string;
		content_type: string;
		content: string | null;
	};

	type ChunkRecord = {
		id: unknown;
		index: number;
		content: string;
		metadata: Record<string, unknown> | null;
	};

	let file = $state<FileRecord | null>(null);
	let chunks = $state<ChunkRecord[]>([]);
	let loading = $state(true);
	let error = $state('');

	$effect(() => {
		const token = $auth.token;
		const fileId = page.params.file_id;
		if (!token || !fileId) {
			loading = false;
			return;
		}

		let cancelled = false;

		(async () => {
			try {
				const db = await getDb(token);
				if (cancelled) return;

				const [fileRes, chunksRes] = await Promise.all([
					db.select<FileRecord>(new RecordId('file', fileId)),
					db.query<[ChunkRecord[]]>(
						'SELECT id, index, content, metadata FROM chunk WHERE doc = $doc ORDER BY index ASC',
						{ doc: new RecordId('file', fileId) }
					)
				]);
				if (cancelled) return;

				file = fileRes ?? null;
				chunks = chunksRes[0] ?? [];
			} catch (err) {
				if (!cancelled) {
					error = err instanceof Error ? err.message : 'Failed to load file';
				}
			} finally {
				if (!cancelled) loading = false;
			}
		})();

		return () => {
			cancelled = true;
		};
	});
</script>

<div class="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8">
	{#if page.params.file_id}
		<MoveFile fileId={page.params.file_id} />
	{/if}

	{#if loading}
		<p class="text-muted-foreground">Loading chunks…</p>
	{:else if error}
		<p class="text-destructive">{error}</p>
	{:else if !$auth.isAuthenticated}
		<p class="text-muted-foreground">Please log in to view file chunks.</p>
	{:else if chunks.length === 0}
		<p class="text-muted-foreground">No chunks found for this file.</p>
	{:else}
		{#if file && file.content_type === 'text/markdown'}
			<Card.Root>
				<Card.Content>
					<pre class="text-wrap">{file.content}</pre>
				</Card.Content>
			</Card.Root>
		{/if}
		<Accordion.Root type="multiple" class="rounded-lg border">
			{#each chunks as chunk (chunk.id?.toString())}
				<Accordion.Item value={chunk.id?.toString() ?? String(chunk.index)}>
					<Accordion.Trigger class="px-4">
						<span class="mr-3 font-mono text-xs text-muted-foreground">#{chunk.index}</span>
						<span class="line-clamp-2 flex-1 text-left font-normal">{chunk.content}</span>
					</Accordion.Trigger>
					<Accordion.Content>
						<p class="px-4 text-sm whitespace-pre-wrap">{chunk.content}</p>
					</Accordion.Content>
				</Accordion.Item>
			{/each}
		</Accordion.Root>
	{/if}
</div>
