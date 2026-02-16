<script lang="ts">
	import { CircleAlert } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { auth } from '$lib/stores/auth';
	import {
		FieldGroup,
		Field,
		FieldLabel,
		FieldDescription
	} from '$lib/components/ui/field/index.js';

	const id = $props.id();

	let mode = $state<'login' | 'signup'>('login');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let errorMessage = $state('');
	let isLoading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		errorMessage = '';
		isLoading = true;

		try {
			const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/signup';
			const body =
				mode === 'signup'
					? { email, password, display_name: displayName || undefined }
					: { email, password };

			const res = await fetch(endpoint, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(body)
			});

			if (!res.ok) {
				const text = await res.text();
				errorMessage = text || `${mode === 'login' ? 'Login' : 'Signup'} failed`;
				return;
			}

			const data = await res.json();
			// Store the JWT token using the auth store
			auth.login(data.token, data.user);

			// Redirect to home page
			await goto(resolve('/'));
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	}

	function toggleMode() {
		mode = mode === 'login' ? 'signup' : 'login';
		errorMessage = '';
	}
</script>

<Card.Root class="mx-auto w-full max-w-sm">
	<Card.Header>
		<Card.Title class="text-2xl">{mode === 'login' ? 'Login' : 'Signup'}</Card.Title>
		<Card.Description
			>{mode === 'login' ? 'Sign in to your account' : 'Sign up to get started'}</Card.Description
		>
	</Card.Header>
	<Card.Content>
		<form onsubmit={handleSubmit}>
			<FieldGroup>
				{#if mode === 'signup'}
					<Field>
						<FieldLabel for="display-{id}">Display name (optional)</FieldLabel>
						<Input id="display-{id}" bind:value={displayName} type="text" placeholder="Your name" />
					</Field>
				{/if}
				<Field>
					<FieldLabel for="email-{id}">Email</FieldLabel>
					<Input
						type="email"
						id="email-{id}"
						bind:value={email}
						placeholder="m@example.com"
						required
					/>
				</Field>
				<Field>
					<div class="flex items-center">
						<FieldLabel for="password-{id}">Password</FieldLabel>
					</div>
					<Input
						id="password-{id}"
						type="password"
						bind:value={password}
						required
						placeholder="••••••••"
					/>
				</Field>

				{#if errorMessage}
					<Alert.Root variant="destructive">
						<CircleAlert />
						<Alert.Title>{errorMessage}</Alert.Title>
					</Alert.Root>
				{/if}

				<Field>
					<Button type="submit" class="w-full" disabled={isLoading}>
						{isLoading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Sign up'}
					</Button>
					<FieldDescription class="text-center">
						{#if mode === 'login'}
							Don't have an account? <a href="##" onclick={toggleMode}>Sign up</a>
						{:else}
							Already have an account? <a href="##" onclick={toggleMode}>Login</a>
						{/if}
					</FieldDescription>
				</Field>
			</FieldGroup>
		</form>
	</Card.Content>
</Card.Root>
