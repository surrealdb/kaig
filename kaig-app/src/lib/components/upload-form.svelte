<script lang="ts">
	import { CircleAlert, CircleCheck, FileUp } from '@lucide/svelte';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { FieldGroup, Field, FieldLabel } from '$lib/components/ui/field/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { auth, getAuthHeader } from '$lib/stores/auth';

	const id = $props.id();

	let fileInput = $state<HTMLInputElement | null>(null);
	let errorMessage = $state('');
	let successMessage = $state('');
	let isLoading = $state(false);
	let dialogOpen = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		errorMessage = '';
		successMessage = '';

		const files = fileInput?.files;
		if (!files || files.length === 0) {
			errorMessage = 'Please select a file';
			return;
		}

		isLoading = true;

		try {
			const formData = new FormData();
			formData.append('file', files[0]);

			const res = await fetch('/api/files/upload', {
				method: 'POST',
				headers: {
					...getAuthHeader()
				},
				body: formData
			});

			if (!res.ok) {
				const text = await res.text();
				errorMessage = text || 'Upload failed';
				return;
			}

			const data = await res.json();
			successMessage = `Uploaded "${data.filename}" successfully`;

			// Reset file input
			if (fileInput) {
				fileInput.value = '';
			}

			// Close dialog
			dialogOpen = false;
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	}
</script>

<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Trigger>
		{#snippet child({ props })}
			<Sidebar.MenuButton {...props}>
				<FileUp size={24} />
				<span>Upload File</span>
			</Sidebar.MenuButton>
		{/snippet}
	</Dialog.Trigger>
	<Dialog.Content>
		<Dialog.Header>
			<Dialog.Title>Upload File</Dialog.Title>
		</Dialog.Header>

		<p class="text-sm">PDF, Markdown</p>
		{#if !$auth.isAuthenticated}
			<Alert.Root>
				<CircleAlert />
				<Alert.Title>Please log in to upload files.</Alert.Title>
			</Alert.Root>
		{:else}
			<form onsubmit={handleSubmit}>
				<FieldGroup>
					<Field>
						<FieldLabel for="file-{id}">File</FieldLabel>
						<Input id="file-{id}" type="file" accept=".pdf,.md,.mdx,.mdc" bind:ref={fileInput} />
					</Field>

					{#if errorMessage}
						<Alert.Root variant="destructive">
							<CircleAlert />
							<Alert.Title>{errorMessage}</Alert.Title>
						</Alert.Root>
					{/if}

					{#if successMessage}
						<Alert.Root>
							<CircleCheck />
							<Alert.Title>{successMessage}</Alert.Title>
						</Alert.Root>
					{/if}

					<Field>
						<Button type="submit" class="w-full" disabled={isLoading}>
							{isLoading ? 'Uploading...' : 'Upload'}
						</Button>
					</Field>
				</FieldGroup>
			</form>
		{/if}
	</Dialog.Content>
</Dialog.Root>
