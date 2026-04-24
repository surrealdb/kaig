<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';
	import { SvelteMap } from 'svelte/reactivity';
	import GraphCanvas, { type GraphNode, type GraphLink } from './graph-canvas.svelte';

	type NodeType = 'product' | 'category' | 'order' | 'review' | 'user';
	type EdgeType = 'product_in_order' | 'product_in_category' | 'review_for_product' | 'user_purchased' | 'user_wrote';

	type ProductRecord = { id: unknown; name: string; category: unknown };
	type CategoryRecord = { id: unknown; name: string };
	type OrderRecord = { id: unknown; user: unknown };
	type ReviewRecord = { id: unknown; user: unknown; product: unknown };
	type UserRecord = { id: unknown; name?: string; display_name?: string; email: string };
	type EcommRelRecord = { in: unknown; out: unknown };

	let loading = $state(true);
	let error = $state('');

	let products = $state<ProductRecord[]>([]);
	let categories = $state<CategoryRecord[]>([]);
	let orders = $state<OrderRecord[]>([]);
	let reviews = $state<ReviewRecord[]>([]);
	let users = $state<UserRecord[]>([]);
	let productOrders = $state<EcommRelRecord[]>([]);

	const nodeColor: Record<NodeType, string> = {
		product: '#ec4899',
		category: '#8b5cf6',
		order: '#14b8a6',
		review: '#f59e0b',
		user: '#06b6d4'
	};

	const nodeRadius: Record<NodeType, number> = {
		user: 12,
		product: 10,
		category: 10,
		order: 10,
		review: 7
	};

	const linkColor: Record<EdgeType, string> = {
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

				const [productsRes, categoriesRes, ordersRes, reviewsRes, usersRes, productOrdersRes] =
					await Promise.all([
						db.query<[ProductRecord[]]>('SELECT id, name, category FROM product'),
						db.query<[CategoryRecord[]]>('SELECT id, name FROM category'),
						db.query<[OrderRecord[]]>('SELECT id, user FROM `order`'),
						db.query<[ReviewRecord[]]>('SELECT id, user, product FROM review'),
						db.query<[UserRecord[]]>('SELECT id, name, display_name, email FROM user'),
						db.query<[EcommRelRecord[]]>('SELECT in, out FROM REL_PRODUCT_IN_ORDER')
					]);
				if (cancelled) return;

				products = productsRes[0] ?? [];
				categories = categoriesRes[0] ?? [];
				orders = ordersRes[0] ?? [];
				reviews = reviewsRes[0] ?? [];
				users = usersRes[0] ?? [];
				productOrders = productOrdersRes[0] ?? [];
				loading = false;

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
						const exists = productOrders.some(
							(r) => rid((r as EcommRelRecord & { id?: unknown }).id) === id
						);
						productOrders = exists
							? productOrders.map((r) =>
									rid((r as EcommRelRecord & { id?: unknown }).id) === id ? rec : r
								)
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
