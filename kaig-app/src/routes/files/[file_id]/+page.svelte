<script lang="ts">
	import { page } from '$app/state';
	import MoveFile from '@/components/move-file.svelte';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import { marked } from 'marked';
	import { RecordId, Table } from 'surrealdb';
	import type { LiveSubscription, Surreal } from 'surrealdb';

	import * as Accordion from '$lib/components/ui/accordion';
	import * as Card from '$lib/components/ui/card/index.js';

	type FileRecord = {
		id: RecordId;
		filename: string;
		content_type: string;
		content: string | null;
	};

	type ChunkRecord = {
		id: RecordId;
		doc: RecordId;
		index: number;
		content: string;
		metadata: Record<string, unknown> | null;
	};

	const rid = (r: unknown) => (r == null ? '' : String(r));

	function insertSorted(list: ChunkRecord[], rec: ChunkRecord): ChunkRecord[] {
		const next = list.slice();
		let i = 0;
		while (i < next.length && next[i].index <= rec.index) i++;
		next.splice(i, 0, rec);
		return next;
	}

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

		const recordId = new RecordId('file', fileId);
		const recordIdStr = String(recordId);

		let cancelled = false;
		let db: Surreal | null = null;
		let fileSub: LiveSubscription | null = null;
		let chunkSub: LiveSubscription | null = null;
		let unsubFile: (() => void) | null = null;
		let unsubChunk: (() => void) | null = null;

		(async () => {
			try {
				db = await getDb(token);
				if (cancelled) return;

				const [fileRes, chunksRes] = await Promise.all([
					db.select<FileRecord>(recordId),
					db.query<[ChunkRecord[]]>(
						'SELECT id, doc, index, content, metadata FROM chunk WHERE doc = $doc ORDER BY index ASC',
						{ doc: recordId }
					)
				]);
				if (cancelled) return;

				file = fileRes ?? null;
				chunks = chunksRes[0] ?? [];
				loading = false;

				fileSub = await db.live<FileRecord>(new Table('file'));
				if (cancelled) {
					fileSub.kill().catch(() => {});
					return;
				}
				unsubFile = fileSub.subscribe((message) => {
					if (String(message.recordId) !== recordIdStr) return;
					if (message.action === 'UPDATE' || message.action === 'CREATE') {
						file = message.value as FileRecord;
					} else if (message.action === 'DELETE') {
						file = null;
					}
				});

				chunkSub = await db.live<ChunkRecord>(new Table('chunk'));
				if (cancelled) {
					chunkSub.kill().catch(() => {});
					return;
				}
				unsubChunk = chunkSub.subscribe((message) => {
					const msgIdStr = String(message.recordId);
					if (message.action === 'DELETE') {
						chunks = chunks.filter((c) => rid(c.id) !== msgIdStr);
						return;
					}
					const rec = message.value as ChunkRecord | undefined;
					if (!rec) return;
					const belongs = rid(rec.doc) === recordIdStr;
					const exists = chunks.some((c) => rid(c.id) === msgIdStr);
					if (message.action === 'CREATE') {
						if (belongs && !exists) chunks = insertSorted(chunks, rec);
					} else if (message.action === 'UPDATE') {
						if (belongs) {
							if (exists) {
								chunks = chunks.map((c) => (rid(c.id) === msgIdStr ? rec : c));
							} else {
								chunks = insertSorted(chunks, rec);
							}
						} else if (exists) {
							chunks = chunks.filter((c) => rid(c.id) !== msgIdStr);
						}
					}
				});
			} catch (err) {
				if (!cancelled) {
					error = err instanceof Error ? err.message : 'Failed to load file';
					loading = false;
				}
			}
		})();

		return () => {
			cancelled = true;
			loading = false;
			if (unsubFile) unsubFile();
			if (unsubChunk) unsubChunk();
			if (fileSub) fileSub.kill().catch(() => {});
			if (chunkSub) chunkSub.kill().catch(() => {});
		};
	});
</script>

<div class="mx-auto flex w-full flex-col gap-6 px-4 py-8">
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
					<div class="file_content text-wrap">{@html marked.parse(file.content || '')}</div>
				</Card.Content>
			</Card.Root>
		{:else if file && file.content_type === 'text/html'}
			<Card.Root class="overflow-hidden p-0">
				<Card.Content class="p-0">
					<iframe
						srcdoc={file.content || ''}
						sandbox="allow-scripts"
						class="h-screen w-full rounded-lg border-0"
						title={file.filename}
					></iframe>
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

<style>
	.file_content :global {
		p {
			margin-bottom: 1rem;
		}
		ul,
		ol {
			display: block;
			list-style: disc outside none;
			margin: 1em 0;
			padding: 0 0 0 40px;
		}
		ol {
			list-style-type: decimal;
		}

		li {
			display: list-item;
		}

		ul ul,
		ol ul {
			list-style-type: circle;
			margin-left: 15px;
		}
		ol ol,
		ul ol {
			list-style-type: lower-latin;
			margin-left: 15px;
		}
	}
</style>
