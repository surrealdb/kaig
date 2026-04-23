<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';
	import { SvelteMap } from 'svelte/reactivity';
	import GraphCanvas, { type GraphNode, type GraphLink } from './graph-canvas.svelte';

	type NodeType = 'file' | 'folder' | 'chunk' | 'keyword';
	type EdgeType = 'parent' | 'doc' | 'has_keyword';

	type FileRecord = {
		id: unknown;
		filename: string;
		content_type: string;
		parent: unknown;
		deleted_at: unknown;
	};
	type ChunkRecord = { id: unknown; doc: unknown; index: number };
	type KeywordRecord = { id: unknown };
	type RelRecord = { in: unknown; out: unknown };

	let loading = $state(true);
	let error = $state('');

	let files = $state<FileRecord[]>([]);
	let chunks = $state<ChunkRecord[]>([]);
	let keywords = $state<KeywordRecord[]>([]);
	let rels = $state<RelRecord[]>([]);

	const nodeColor: Record<NodeType, string> = {
		folder: '#a855f7',
		file: '#3b82f6',
		chunk: '#22c55e',
		keyword: '#f97316'
	};

	const nodeRadius: Record<NodeType, number> = {
		folder: 12,
		file: 10,
		chunk: 7,
		keyword: 5
	};

	const linkColor: Record<EdgeType, string> = {
		parent: '#6b7280',
		doc: '#22c55e',
		has_keyword: '#f97316'
	};

	function rid(r: unknown): string {
		if (r == null) return '';
		if (typeof r === 'string') return r;
		if (typeof (r as { toString?: () => string }).toString === 'function')
			return (r as { toString: () => string }).toString();
		return String(r);
	}

	let graphData = $derived.by(() => {
		const nodesMap = new SvelteMap<string, GraphNode>();

		for (const f of files) {
			if (f.deleted_at) continue;
			const id = rid(f.id);
			nodesMap.set(id, {
				id,
				label: f.filename ?? id,
				type: f.content_type === 'folder' ? 'folder' : 'file'
			});
		}

		for (const c of chunks) {
			const id = rid(c.id);
			nodesMap.set(id, { id, label: `num:${c.index}`, type: 'chunk' });
		}

		for (const k of keywords) {
			const id = rid(k.id);
			nodesMap.set(id, { id, label: id.split(':')[1] ?? id, type: 'keyword' });
		}

		const nodes = Array.from(nodesMap.values());
		const links: GraphLink[] = [];

		for (const f of files) {
			if (f.deleted_at) continue;
			if (f.parent) {
				const src = rid(f.id);
				const tgt = rid(f.parent);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'parent' });
				}
			}
		}

		for (const c of chunks) {
			if (c.doc) {
				const src = rid(c.id);
				const tgt = rid(c.doc);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'doc' });
				}
			}
		}

		for (const r of rels) {
			const src = rid(r.in);
			const tgt = rid(r.out);
			if (nodesMap.has(src) && nodesMap.has(tgt)) {
				links.push({ source: src, target: tgt, type: 'has_keyword' });
			}
		}

		return { nodes, links };
	});

	$effect(() => {
		const token = $auth.token;
		if (!token) {
			loading = false;
			return;
		}

		let cancelled = false;
		let subscriptions: LiveSubscription[] = [];
		let db: Surreal | null = null;

		(async () => {
			try {
				db = await getDb(token);
				if (cancelled) return;

				const [filesRes, chunksRes, keywordsRes, relsRes] = await Promise.all([
					db.query<[FileRecord[]]>(
						'SELECT id, filename, content_type, parent, deleted_at FROM file WHERE deleted_at = NONE'
					),
					db.query<[ChunkRecord[]]>('SELECT id, doc, index FROM chunk'),
					db.query<[KeywordRecord[]]>('SELECT id FROM keyword'),
					db.query<[RelRecord[]]>('SELECT in, out FROM REL_FILE_HAS_KEYWORD')
				]);
				if (cancelled) return;

				files = filesRes[0] ?? [];
				chunks = chunksRes[0] ?? [];
				keywords = keywordsRes[0] ?? [];
				rels = relsRes[0] ?? [];
				loading = false;

				const fileSub = await db.live<FileRecord>(new Table('file'));
				if (cancelled) { fileSub.kill().catch(() => {}); return; }
				subscriptions.push(fileSub);
				fileSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						const rec = msg.value as FileRecord;
						if (!rec.deleted_at) files = [rec, ...files];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						files = files.filter((f) => rid(f.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as FileRecord;
						const id = String(msg.recordId);
						if (rec.deleted_at) {
							files = files.filter((f) => rid(f.id) !== id);
						} else {
							const exists = files.some((f) => rid(f.id) === id);
							files = exists ? files.map((f) => (rid(f.id) === id ? rec : f)) : [rec, ...files];
						}
					}
				});

				const chunkSub = await db.live<ChunkRecord>(new Table('chunk'));
				if (cancelled) { chunkSub.kill().catch(() => {}); return; }
				subscriptions.push(chunkSub);
				chunkSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						chunks = [msg.value as ChunkRecord, ...chunks];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						chunks = chunks.filter((c) => rid(c.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as ChunkRecord;
						const id = String(msg.recordId);
						const exists = chunks.some((c) => rid(c.id) === id);
						chunks = exists ? chunks.map((c) => (rid(c.id) === id ? rec : c)) : [rec, ...chunks];
					}
				});

				const kwSub = await db.live<KeywordRecord>(new Table('keyword'));
				if (cancelled) { kwSub.kill().catch(() => {}); return; }
				subscriptions.push(kwSub);
				kwSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						keywords = [msg.value as KeywordRecord, ...keywords];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						keywords = keywords.filter((k) => rid(k.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as KeywordRecord;
						const id = String(msg.recordId);
						const exists = keywords.some((k) => rid(k.id) === id);
						keywords = exists
							? keywords.map((k) => (rid(k.id) === id ? rec : k))
							: [rec, ...keywords];
					}
				});

				const relSub = await db.live<RelRecord>(new Table('REL_FILE_HAS_KEYWORD'));
				if (cancelled) { relSub.kill().catch(() => {}); return; }
				subscriptions.push(relSub);
				relSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						rels = [msg.value as RelRecord, ...rels];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						rels = rels.filter(
							(r) =>
								rid((r as RelRecord & { id?: unknown }).id) !== id && String(msg.recordId) !== id
						);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as RelRecord;
						const id = String(msg.recordId);
						const exists = rels.some((r) => rid((r as RelRecord & { id?: unknown }).id) === id);
						rels = exists
							? rels.map((r) => (rid((r as RelRecord & { id?: unknown }).id) === id ? rec : r))
							: [rec, ...rels];
					}
				});
			} catch (err) {
				if (!cancelled) {
					error = err instanceof Error ? err.message : 'Failed to load graph';
					loading = false;
				}
			}
		})();

		return () => {
			cancelled = true;
			for (const sub of subscriptions) sub.kill().catch(() => {});
		};
	});
</script>

<GraphCanvas
	nodes={graphData.nodes}
	links={graphData.links}
	{nodeColor}
	{nodeRadius}
	{linkColor}
	{loading}
	{error}
	isAuthenticated={$auth.isAuthenticated}
/>
