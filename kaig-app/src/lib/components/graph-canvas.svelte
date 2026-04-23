<script lang="ts">
	import { tick } from 'svelte';
	import * as d3 from 'd3';

	export interface GraphNode extends d3.SimulationNodeDatum {
		id: string;
		label: string;
		type: string;
	}

	export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
		type: string;
	}

	let {
		nodes,
		links,
		nodeColor,
		linkColor,
		nodeRadius = {},
		loading,
		error,
		isAuthenticated
	}: {
		nodes: GraphNode[];
		links: GraphLink[];
		nodeColor: Record<string, string>;
		linkColor: Record<string, string>;
		nodeRadius?: Record<string, number>;
		loading: boolean;
		error: string;
		isAuthenticated: boolean;
	} = $props();

	// svelte-ignore non_reactive_update
	let svgEl: SVGSVGElement;

	// eslint-disable-next-line svelte/prefer-svelte-reactivity
	let positionCache = new Map<string, { x: number; y: number }>();
	let sim: d3.Simulation<GraphNode, GraphLink> | null = null;
	let linkGroup: d3.Selection<SVGGElement, unknown, null, undefined> | null = null;
	let nodeGroup: d3.Selection<SVGGElement, unknown, null, undefined> | null = null;

	$effect(() => {
		if (!loading && svgEl) {
			tick().then(() => updateGraph(nodes, links));
		}
	});

	function pinAllNodes() {
		if (!sim) return;
		for (const d of sim.nodes()) {
			d.fx = d.x;
			d.fy = d.y;
			if (d.x != null && d.y != null) positionCache.set(d.id, { x: d.x, y: d.y });
		}
	}

	function updateGraph(nodes: GraphNode[], links: GraphLink[]) {
		const rect = svgEl.getBoundingClientRect();
		const width = rect.width || window.innerWidth;
		const height = rect.height || window.innerHeight;

		const isFirstRender = sim === null;

		if (isFirstRender) {
			const svg = d3.select(svgEl);
			const g = svg.append('g');

			svg.call(
				d3
					.zoom<SVGSVGElement, unknown>()
					.scaleExtent([0.1, 4])
					.on('zoom', (e) => g.attr('transform', e.transform))
			);

			linkGroup = g.append('g') as d3.Selection<SVGGElement, unknown, null, undefined>;
			nodeGroup = g.append('g') as d3.Selection<SVGGElement, unknown, null, undefined>;

			sim = d3
				.forceSimulation<GraphNode>()
				.force(
					'link',
					d3
						.forceLink<GraphNode, GraphLink>()
						.id((d) => d.id)
						.distance(80)
				)
				.force('charge', d3.forceManyBody().strength(-200))
				.force('center', d3.forceCenter(width / 2, height / 2))
				.force('collision', d3.forceCollide(18))
				.on('end', pinAllNodes);
		} else {
			for (const d of sim!.nodes()) {
				if (d.x != null && d.y != null) positionCache.set(d.id, { x: d.x, y: d.y });
			}
		}

		for (const node of nodes) {
			const cached = positionCache.get(node.id);
			if (cached) {
				node.x = cached.x;
				node.y = cached.y;
				node.fx = cached.x;
				node.fy = cached.y;
			}
		}

		sim!.nodes(nodes);
		(sim!.force('link') as d3.ForceLink<GraphNode, GraphLink>).links(links);

		const linkSel = linkGroup!
			.selectAll<SVGLineElement, GraphLink>('line')
			.data(links, (d) => {
				const s = typeof d.source === 'object' ? (d.source as GraphNode).id : String(d.source);
				const t = typeof d.target === 'object' ? (d.target as GraphNode).id : String(d.target);
				return `${s}→${t}`;
			})
			.join('line')
			.attr('stroke', (d) => linkColor[d.type])
			.attr('stroke-opacity', 0.5)
			.attr('stroke-width', 1.5);

		const nodeSel = nodeGroup!
			.selectAll<SVGGElement, GraphNode>('g')
			.data(nodes, (d) => d.id)
			.join(
				(enter) => {
					const g = enter.append('g').call(
						d3
							.drag<SVGGElement, GraphNode>()
							.on('start', (e, d) => {
								if (!e.active) sim!.alphaTarget(0.3).restart();
								d.fx = d.x;
								d.fy = d.y;
							})
							.on('drag', (e, d) => {
								d.fx = e.x;
								d.fy = e.y;
							})
							.on('end', (e, d) => {
								if (!e.active) sim!.alphaTarget(0);
								d.fx = d.x;
								d.fy = d.y;
							})
					);

					g.append('circle')
						.attr('r', (d) => nodeRadius[d.type] ?? 8)
						.attr('fill', (d) => nodeColor[d.type])
						.attr('stroke', '#fff')
						.attr('stroke-width', 1.5);

					g.append('text')
						.text((d) => (d.label.length > 20 ? d.label.slice(0, 18) + '…' : d.label))
						.attr('x', 15)
						.attr('y', 4)
						.attr('font-size', '11px')
						.attr('fill', 'currentColor')
						.style('pointer-events', 'none')
						.style('user-select', 'none');

					g.append('title').text((d) => `${d.type}: ${d.label}`);

					return g;
				},
				(update) => update,
				(exit) => exit.remove()
			);

		sim!.on('tick', () => {
			linkSel
				.attr('x1', (d) => (d.source as GraphNode).x!)
				.attr('y1', (d) => (d.source as GraphNode).y!)
				.attr('x2', (d) => (d.target as GraphNode).x!)
				.attr('y2', (d) => (d.target as GraphNode).y!);

			nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);

			for (const d of sim!.nodes()) {
				if (d.x != null && d.y != null) positionCache.set(d.id, { x: d.x, y: d.y });
			}
		});

		if (isFirstRender) {
			sim!.alpha(1).restart();
		} else {
			sim!.alpha(0.1).restart();
		}
	}
</script>

{#if loading}
	<div class="flex h-full items-center justify-center text-muted-foreground">Loading graph…</div>
{:else if error}
	<div class="flex h-full items-center justify-center text-destructive">{error}</div>
{:else if !isAuthenticated}
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
