<script lang="ts">
	import Graph from '@/components/graph.svelte';
	import GraphEcomm from '@/components/graph-ecomm.svelte';

	let active = $state<'files' | 'ecomm'>('files');
</script>

<div class="relative w-full" style="height: calc(100dvh - 36px)">
	<div
		class="absolute top-3 left-1/2 z-10 flex -translate-x-1/2 gap-1 rounded-lg border bg-background/80 p-1 backdrop-blur-sm"
	>
		<button
			class="rounded-md px-3 py-1 text-xs font-medium transition-colors {active === 'files'
				? 'bg-foreground text-background'
				: 'text-muted-foreground hover:text-foreground'}"
			onclick={() => (active = 'files')}
		>
			Files
		</button>
		<button
			class="rounded-md px-3 py-1 text-xs font-medium transition-colors {active === 'ecomm'
				? 'bg-foreground text-background'
				: 'text-muted-foreground hover:text-foreground'}"
			onclick={() => (active = 'ecomm')}
		>
			E-commerce
		</button>
	</div>

	{#if active === 'files'}
		<Graph />
	{:else}
		<GraphEcomm />
	{/if}
</div>
