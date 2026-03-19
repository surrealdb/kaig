<script lang="ts">
	import { tick } from 'svelte';
	import * as d3 from 'd3';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';

	type NodeType = 'file' | 'folder' | 'chunk' | 'keyword';
	type EdgeType = 'parent' | 'doc' | 'has_keyword';

	interface GraphNode extends d3.SimulationNodeDatum {
		id: string;
		label: string;
		type: NodeType;
	}

	interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
		type: EdgeType;
	}

	type FileRecord = { id: unknown; filename: string; content_type: string; parent: unknown; deleted_at: unknown };
	type ChunkRecord = { id: unknown; doc: unknown };
	type KeywordRecord = { id: unknown };
	type RelRecord = { in: unknown; out: unknown };

	let svgEl: SVGSVGElement;
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
		const nodesMap = new Map<string, GraphNode>();

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
			nodesMap.set(id, {
				id,
				label: id.split(':')[1]?.slice(0, 6) ?? id,
				type: 'chunk'
			});
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
					db.query<[FileRecord[]]>('SELECT id, filename, content_type, parent, deleted_at FROM file WHERE deleted_at = NONE'),
					db.query<[ChunkRecord[]]>('SELECT id, doc FROM chunk'),
					db.query<[KeywordRecord[]]>('SELECT id FROM keyword'),
					db.query<[RelRecord[]]>('SELECT in, out FROM REL_FILE_HAS_KEYWORD')
				]);
				if (cancelled) return;

				files = filesRes[0] ?? [];
				chunks = chunksRes[0] ?? [];
				keywords = keywordsRes[0] ?? [];
				rels = relsRes[0] ?? [];
				loading = false;

				// LIVE: file
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

				// LIVE: chunk
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

				// LIVE: keyword
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

				// LIVE: REL_FILE_HAS_KEYWORD
				const relSub = await db.live<RelRecord>(new Table('REL_FILE_HAS_KEYWORD'));
				if (cancelled) { relSub.kill().catch(() => {}); return; }
				subscriptions.push(relSub);
				relSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						rels = [msg.value as RelRecord, ...rels];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						rels = rels.filter((r) => rid((r as RelRecord & { id?: unknown }).id) !== id && String(msg.recordId) !== id);
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

	$effect(() => {
		const { nodes, links } = graphData;
		if (!loading && svgEl) {
			tick().then(() => initGraph(nodes, links));
		}
	});

	function initGraph(nodes: GraphNode[], links: GraphLink[]) {
		const rect = svgEl.getBoundingClientRect();
		const width = rect.width || window.innerWidth;
		const height = rect.height || window.innerHeight;

		const svg = d3.select(svgEl);
		svg.selectAll('*').remove();

		const g = svg.append('g');

		svg.call(
			d3
				.zoom<SVGSVGElement, unknown>()
				.scaleExtent([0.1, 4])
				.on('zoom', (e) => g.attr('transform', e.transform))
		);

		const simulation = d3
			.forceSimulation<GraphNode>(nodes)
			.force(
				'link',
				d3
					.forceLink<GraphNode, GraphLink>(links)
					.id((d) => d.id)
					.distance(80)
			)
			.force('charge', d3.forceManyBody().strength(-200))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide(18));

		const link = g
			.append('g')
			.selectAll('line')
			.data(links)
			.join('line')
			.attr('stroke', (d) => linkColor[d.type])
			.attr('stroke-opacity', 0.5)
			.attr('stroke-width', 1.5);

		const node = g
			.append('g')
			.selectAll<SVGGElement, GraphNode>('g')
			.data(nodes)
			.join('g')
			.call(
				d3
					.drag<SVGGElement, GraphNode>()
					.on('start', (e, d) => {
						if (!e.active) simulation.alphaTarget(0.3).restart();
						d.fx = d.x;
						d.fy = d.y;
					})
					.on('drag', (e, d) => {
						d.fx = e.x;
						d.fy = e.y;
					})
					.on('end', (e, d) => {
						if (!e.active) simulation.alphaTarget(0);
						d.fx = null;
						d.fy = null;
					})
			);

		node
			.append('circle')
			.attr('r', (d) =>
				d.type === 'folder' ? 12 : d.type === 'file' ? 10 : d.type === 'chunk' ? 7 : 5
			)
			.attr('fill', (d) => nodeColor[d.type])
			.attr('stroke', '#fff')
			.attr('stroke-width', 1.5);

		node
			.filter((d) => d.type === 'file' || d.type === 'folder' || d.type === 'keyword')
			.append('text')
			.text((d) => (d.label.length > 20 ? d.label.slice(0, 18) + '…' : d.label))
			.attr('x', 15)
			.attr('y', 4)
			.attr('font-size', '11px')
			.attr('fill', 'currentColor')
			.style('pointer-events', 'none')
			.style('user-select', 'none');

		node.append('title').text((d) => `${d.type}: ${d.label}`);

		simulation.on('tick', () => {
			link
				.attr('x1', (d) => (d.source as GraphNode).x!)
				.attr('y1', (d) => (d.source as GraphNode).y!)
				.attr('x2', (d) => (d.target as GraphNode).x!)
				.attr('y2', (d) => (d.target as GraphNode).y!);

			node.attr('transform', (d) => `translate(${d.x},${d.y})`);
		});
	}
</script>

<div class="relative w-full" style="height: calc(100dvh - 36px)">
	{#if loading}
		<div class="flex h-full items-center justify-center text-muted-foreground">Loading graph…</div>
	{:else if error}
		<div class="flex h-full items-center justify-center text-destructive">{error}</div>
	{:else if !$auth.isAuthenticated}
		<div class="flex h-full items-center justify-center text-muted-foreground">
			Please log in to view the knowledge graph.
		</div>
	{:else}
		<svg bind:this={svgEl} class="h-full w-full" />
		<div
			class="absolute bottom-4 left-4 flex flex-col gap-1.5 rounded-lg border bg-background/80 p-3 text-xs backdrop-blur-sm"
		>
			{#each Object.entries(nodeColor) as [type, color] (type)}
				<span class="flex items-center gap-2">
					<span class="inline-block h-3 w-3 rounded-full" style:background={color}></span>
					{type}
				</span>
			{/each}
		</div>
	{/if}
</div>
