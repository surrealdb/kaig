<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import * as Card from '$lib/components/ui/card/index.js';

	type ProductRecord = {
		id: unknown;
		name: string;
		description: string;
		price: number;
		category: unknown;
	};

	let products = $state<ProductRecord[]>([]);
	let loading = $state(true);
	let error = $state('');

	$effect(() => {
		const token = $auth.token;
		if (!token) {
			loading = false;
			return;
		}

		let cancelled = false;

		(async () => {
			try {
				const db = await getDb(token);
				if (cancelled) return;

				const [result] = await db.query<[ProductRecord[]]>(
					'SELECT id, name, description, price, category FROM product ORDER BY name ASC'
				);
				if (!cancelled) products = result ?? [];
			} catch (err) {
				if (!cancelled) error = err instanceof Error ? err.message : 'Failed to load products';
			} finally {
				if (!cancelled) loading = false;
			}
		})();

		return () => {
			cancelled = true;
		};
	});
</script>

<div class="mx-auto flex w-full flex-col gap-6 px-4 py-8">
	<h1 class="text-2xl font-semibold">Products</h1>

	{#if loading}
		<p class="text-muted-foreground">Loading products…</p>
	{:else if error}
		<p class="text-destructive">{error}</p>
	{:else if !$auth.isAuthenticated}
		<p class="text-muted-foreground">Please log in to view products.</p>
	{:else if products.length === 0}
		<p class="text-muted-foreground">No products found.</p>
	{:else}
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each products as product (product.id?.toString())}
				<Card.Root>
					<Card.Header>
						<Card.Title>{product.name}</Card.Title>
						<Card.Description class="font-medium">${product.price.toFixed(2)}</Card.Description>
					</Card.Header>
					<Card.Content>
						<p class="text-sm text-muted-foreground">{product.description}</p>
					</Card.Content>
				</Card.Root>
			{/each}
		</div>
	{/if}
</div>
