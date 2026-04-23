<script lang="ts">
	import { tick } from 'svelte';
	import * as d3 from 'd3';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';
	import { SvelteMap } from 'svelte/reactivity';

	type NodeType = 'file' | 'folder' | 'chunk' | 'keyword' | 'product' | 'category' | 'order' | 'review' | 'user';
	type EdgeType = 'parent' | 'doc' | 'has_keyword' | 'product_in_order' | 'product_in_category' | 'review_for_product' | 'user_purchased' | 'user_wrote';

	interface GraphNode extends d3.SimulationNodeDatum {
		id: string;
		label: string;
		type: NodeType;
	}

	interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
		type: EdgeType;
	}

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
	type ProductRecord = { id: unknown; name: string; category: unknown };
	type CategoryRecord = { id: unknown; name: string };
	type OrderRecord = { id: unknown; user: unknown };
	type ReviewRecord = { id: unknown; user: unknown; product: unknown };
	type UserRecord = { id: unknown; name?: string; display_name?: string; email: string };
	type EcommRelRecord = { in: unknown; out: unknown };

	// svelte-ignore non_reactive_update
	let svgEl: SVGSVGElement;
	let loading = $state(true);
	let error = $state('');

	// Persistent graph state — survives graphData re-derives
	// eslint-disable-next-line svelte/prefer-svelte-reactivity
	let positionCache = new Map<string, { x: number; y: number }>();
	let sim: d3.Simulation<GraphNode, GraphLink> | null = null;
	let linkGroup: d3.Selection<SVGGElement, unknown, null, undefined> | null = null;
	let nodeGroup: d3.Selection<SVGGElement, unknown, null, undefined> | null = null;

	let files = $state<FileRecord[]>([]);
	let chunks = $state<ChunkRecord[]>([]);
	let keywords = $state<KeywordRecord[]>([]);
	let rels = $state<RelRecord[]>([]);
	let products = $state<ProductRecord[]>([]);
	let categories = $state<CategoryRecord[]>([]);
	let orders = $state<OrderRecord[]>([]);
	let reviews = $state<ReviewRecord[]>([]);
	let users = $state<UserRecord[]>([]);
	let productOrders = $state<EcommRelRecord[]>([]);

	const nodeColor: Record<NodeType, string> = {
		folder: '#a855f7',
		file: '#3b82f6',
		chunk: '#22c55e',
		keyword: '#f97316',
		product: '#ec4899',
		category: '#8b5cf6',
		order: '#14b8a6',
		review: '#f59e0b',
		user: '#06b6d4'
	};

	const linkColor: Record<EdgeType, string> = {
		parent: '#6b7280',
		doc: '#22c55e',
		has_keyword: '#f97316',
		product_in_order: '#14b8a6',
		product_in_category: '#8b5cf6',
		review_for_product: '#f59e0b',
		user_purchased: '#06b6d4',
		user_wrote: '#06b6d4'
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
			nodesMap.set(id, {
				id,
				// label: `num:${c.index} - ` + (id.split(':')[1]?.slice(0, 6) ?? id),
				label: `num:${c.index}`,
				type: 'chunk'
			});
		}

		for (const k of keywords) {
			const id = rid(k.id);
			nodesMap.set(id, { id, label: id.split(':')[1] ?? id, type: 'keyword' });
		}

		for (const p of products) {
			const id = rid(p.id);
			nodesMap.set(id, { id, label: p.name ?? id, type: 'product' });
		}

		for (const c of categories) {
			const id = rid(c.id);
			nodesMap.set(id, { id, label: c.name ?? id, type: 'category' });
		}

		for (const o of orders) {
			const id = rid(o.id);
			nodesMap.set(id, { id, label: id.split(':')[1] ?? id, type: 'order' });
		}

		for (const rv of reviews) {
			const id = rid(rv.id);
			nodesMap.set(id, { id, label: id.split(':')[1] ?? id, type: 'review' });
		}

		for (const u of users) {
			const id = rid(u.id);
			nodesMap.set(id, { id, label: u.display_name ?? u.name ?? u.email ?? id, type: 'user' });
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

		for (const r of productOrders) {
			const src = rid(r.in);
			const tgt = rid(r.out);
			if (nodesMap.has(src) && nodesMap.has(tgt)) {
				links.push({ source: src, target: tgt, type: 'product_in_order' });
			}
		}

		for (const p of products) {
			if (p.category) {
				const src = rid(p.id);
				const tgt = rid(p.category);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'product_in_category' });
				}
			}
		}

		for (const rv of reviews) {
			if (rv.product) {
				const src = rid(rv.id);
				const tgt = rid(rv.product);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'review_for_product' });
				}
			}
			if (rv.user) {
				const src = rid(rv.user);
				const tgt = rid(rv.id);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'user_wrote' });
				}
			}
		}

		for (const o of orders) {
			if (o.user) {
				const src = rid(o.user);
				const tgt = rid(o.id);
				if (nodesMap.has(src) && nodesMap.has(tgt)) {
					links.push({ source: src, target: tgt, type: 'user_purchased' });
				}
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

				const [filesRes, chunksRes, keywordsRes, relsRes, productsRes, categoriesRes, ordersRes, reviewsRes, usersRes, productOrdersRes] = await Promise.all([
					db.query<[FileRecord[]]>(
						'SELECT id, filename, content_type, parent, deleted_at FROM file WHERE deleted_at = NONE'
					),
					db.query<[ChunkRecord[]]>('SELECT id, doc, index FROM chunk'),
					db.query<[KeywordRecord[]]>('SELECT id FROM keyword'),
					db.query<[RelRecord[]]>('SELECT in, out FROM REL_FILE_HAS_KEYWORD'),
					db.query<[ProductRecord[]]>('SELECT id, name, category FROM product'),
					db.query<[CategoryRecord[]]>('SELECT id, name FROM category'),
					db.query<[OrderRecord[]]>('SELECT id, user FROM `order`'),
					db.query<[ReviewRecord[]]>('SELECT id, user, product FROM review'),
					db.query<[UserRecord[]]>('SELECT id, name, display_name, email FROM user'),
					db.query<[EcommRelRecord[]]>('SELECT in, out FROM REL_PRODUCT_IN_ORDER')
				]);
				if (cancelled) return;

				files = filesRes[0] ?? [];
				chunks = chunksRes[0] ?? [];
				keywords = keywordsRes[0] ?? [];
				rels = relsRes[0] ?? [];
				products = productsRes[0] ?? [];
				categories = categoriesRes[0] ?? [];
				orders = ordersRes[0] ?? [];
				reviews = reviewsRes[0] ?? [];
				users = usersRes[0] ?? [];
				productOrders = productOrdersRes[0] ?? [];
				loading = false;

				// LIVE: file
				const fileSub = await db.live<FileRecord>(new Table('file'));
				if (cancelled) {
					fileSub.kill().catch(() => {});
					return;
				}
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
				if (cancelled) {
					chunkSub.kill().catch(() => {});
					return;
				}
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
				if (cancelled) {
					kwSub.kill().catch(() => {});
					return;
				}
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
				if (cancelled) {
					relSub.kill().catch(() => {});
					return;
				}
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

				// LIVE: product
				const productSub = await db.live<ProductRecord>(new Table('product'));
				if (cancelled) { productSub.kill().catch(() => {}); return; }
				subscriptions.push(productSub);
				productSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						products = [msg.value as ProductRecord, ...products];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						products = products.filter((p) => rid(p.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as ProductRecord;
						const id = String(msg.recordId);
						const exists = products.some((p) => rid(p.id) === id);
						products = exists ? products.map((p) => (rid(p.id) === id ? rec : p)) : [rec, ...products];
					}
				});

				// LIVE: category
				const categorySub = await db.live<CategoryRecord>(new Table('category'));
				if (cancelled) { categorySub.kill().catch(() => {}); return; }
				subscriptions.push(categorySub);
				categorySub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						categories = [msg.value as CategoryRecord, ...categories];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						categories = categories.filter((c) => rid(c.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as CategoryRecord;
						const id = String(msg.recordId);
						const exists = categories.some((c) => rid(c.id) === id);
						categories = exists ? categories.map((c) => (rid(c.id) === id ? rec : c)) : [rec, ...categories];
					}
				});

				// LIVE: order
				const orderSub = await db.live<OrderRecord>(new Table('order'));
				if (cancelled) { orderSub.kill().catch(() => {}); return; }
				subscriptions.push(orderSub);
				orderSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						orders = [msg.value as OrderRecord, ...orders];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						orders = orders.filter((o) => rid(o.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as OrderRecord;
						const id = String(msg.recordId);
						const exists = orders.some((o) => rid(o.id) === id);
						orders = exists ? orders.map((o) => (rid(o.id) === id ? rec : o)) : [rec, ...orders];
					}
				});

				// LIVE: review
				const reviewSub = await db.live<ReviewRecord>(new Table('review'));
				if (cancelled) { reviewSub.kill().catch(() => {}); return; }
				subscriptions.push(reviewSub);
				reviewSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						reviews = [msg.value as ReviewRecord, ...reviews];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						reviews = reviews.filter((r) => rid(r.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as ReviewRecord;
						const id = String(msg.recordId);
						const exists = reviews.some((r) => rid(r.id) === id);
						reviews = exists ? reviews.map((r) => (rid(r.id) === id ? rec : r)) : [rec, ...reviews];
					}
				});

				// LIVE: user
				const userSub = await db.live<UserRecord>(new Table('user'));
				if (cancelled) { userSub.kill().catch(() => {}); return; }
				subscriptions.push(userSub);
				userSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						users = [msg.value as UserRecord, ...users];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						users = users.filter((u) => rid(u.id) !== id);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as UserRecord;
						const id = String(msg.recordId);
						const exists = users.some((u) => rid(u.id) === id);
						users = exists ? users.map((u) => (rid(u.id) === id ? rec : u)) : [rec, ...users];
					}
				});

				// LIVE: REL_PRODUCT_IN_ORDER
				const productOrderSub = await db.live<EcommRelRecord>(new Table('REL_PRODUCT_IN_ORDER'));
				if (cancelled) { productOrderSub.kill().catch(() => {}); return; }
				subscriptions.push(productOrderSub);
				productOrderSub.subscribe((msg) => {
					if (msg.action === 'CREATE') {
						productOrders = [msg.value as EcommRelRecord, ...productOrders];
					} else if (msg.action === 'DELETE') {
						const id = String(msg.recordId);
						productOrders = productOrders.filter(
							(r) => rid((r as EcommRelRecord & { id?: unknown }).id) !== id
						);
					} else if (msg.action === 'UPDATE') {
						const rec = msg.value as EcommRelRecord;
						const id = String(msg.recordId);
						const exists = productOrders.some((r) => rid((r as EcommRelRecord & { id?: unknown }).id) === id);
						productOrders = exists
							? productOrders.map((r) => (rid((r as EcommRelRecord & { id?: unknown }).id) === id ? rec : r))
							: [rec, ...productOrders];
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
			// Save current positions before updating
			for (const d of sim!.nodes()) {
				if (d.x != null && d.y != null) positionCache.set(d.id, { x: d.x, y: d.y });
			}
		}

		// Restore cached positions and pin existing nodes; new nodes start near center
		for (const node of nodes) {
			const cached = positionCache.get(node.id);
			if (cached) {
				node.x = cached.x;
				node.y = cached.y;
				node.fx = cached.x;
				node.fy = cached.y;
			}
		}

		// Update simulation data
		sim!.nodes(nodes);
		(sim!.force('link') as d3.ForceLink<GraphNode, GraphLink>).links(links);

		// Update links via join
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

		// Update nodes via join
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
								// Pin node at dropped position
								d.fx = d.x;
								d.fy = d.y;
							})
					);

					g.append('circle')
						.attr('r', (d) => {
							if (d.type === 'folder' || d.type === 'user') return 12;
							if (d.type === 'file' || d.type === 'product' || d.type === 'category' || d.type === 'order') return 10;
							if (d.type === 'chunk' || d.type === 'review') return 7;
							return 5;
						})
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

			// Keep cache current during simulation
			for (const d of sim!.nodes()) {
				if (d.x != null && d.y != null) positionCache.set(d.id, { x: d.x, y: d.y });
			}
		});

		if (isFirstRender) {
			sim!.alpha(1).restart();
		} else {
			// Only new (unpinned) nodes need to find their place
			sim!.alpha(0.1).restart();
		}
	}
</script>

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
