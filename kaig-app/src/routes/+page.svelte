<script lang="ts">
	import { onMount, tick } from 'svelte';
	import * as d3 from 'd3';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';

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

	let svgEl: SVGSVGElement;
	let loading = $state(true);
	let error = $state('');

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

	onMount(async () => {
		if (!$auth.isAuthenticated || !$auth.token) {
			loading = false;
			return;
		}

		try {
			const db = await getDb($auth.token);
			const [files, chunks, keywords, rels] = await Promise.all([
				db.query<[{ id: unknown; filename: string; content_type: string; parent: unknown }[]]>(
					'SELECT id, filename, content_type, parent FROM file'
				),
				db.query<[{ id: unknown; doc: unknown }[]]>('SELECT id, doc FROM chunk'),
				db.query<[{ id: unknown }[]]>('SELECT id FROM keyword'),
				db.query<[{ in: unknown; out: unknown }[]]>('SELECT in, out FROM REL_FILE_HAS_KEYWORD')
			]);

			const nodesMap = new Map<string, GraphNode>();

			for (const f of files[0] ?? []) {
				const id = rid(f.id);
				nodesMap.set(id, {
					id,
					label: f.filename ?? id,
					type: f.content_type === 'folder' ? 'folder' : 'file'
				});
			}

			for (const c of chunks[0] ?? []) {
				const id = rid(c.id);
				nodesMap.set(id, {
					id,
					label: id.split(':')[1]?.slice(0, 6) ?? id,
					type: 'chunk'
				});
			}

			for (const k of keywords[0] ?? []) {
				const id = rid(k.id);
				nodesMap.set(id, { id, label: id.split(':')[1] ?? id, type: 'keyword' });
			}

			const nodes = Array.from(nodesMap.values());
			const links: GraphLink[] = [];

			for (const f of files[0] ?? []) {
				if (f.parent) {
					const src = rid(f.id);
					const tgt = rid(f.parent);
					if (nodesMap.has(src) && nodesMap.has(tgt)) {
						links.push({ source: src, target: tgt, type: 'parent' });
					}
				}
			}

			for (const c of chunks[0] ?? []) {
				if (c.doc) {
					const src = rid(c.id);
					const tgt = rid(c.doc);
					if (nodesMap.has(src) && nodesMap.has(tgt)) {
						links.push({ source: src, target: tgt, type: 'doc' });
					}
				}
			}

			for (const r of rels[0] ?? []) {
				const src = rid(r.in);
				const tgt = rid(r.out);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'has_keyword' });
				}
			}

			loading = false;
			await tick();
			initGraph(nodes, links);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load graph';
			loading = false;
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
			.filter((d) => d.type === 'file' || d.type === 'folder')
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
