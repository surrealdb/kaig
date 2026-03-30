<script lang="ts">
	import { page } from '$app/state';
	import MoveFile from '@/components/move-file.svelte';
</script>

<div class="flex min-h-screen w-full flex-col items-center justify-center gap-4 px-4">
	{#if page.params.file_id}
		<MoveFile fileId={page.params.file_id} />
	{/if}
</div>
