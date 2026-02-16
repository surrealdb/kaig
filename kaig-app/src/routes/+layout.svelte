<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { resolve } from '$app/paths';

	let { children } = $props();

	function handleLogout() {
		auth.logout();
		goto(resolve('/login'));
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Welcome ~</title>
</svelte:head>

{#if page.url.pathname !== '/login'}
	<nav
		class="fixed top-0 right-0 left-0 z-50 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm"
	>
		<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
			<a
				href={resolve('/')}
				class="text-lg font-semibold text-slate-50 transition hover:text-indigo-400"
			>
				Kai G
			</a>
			<div class="flex items-center gap-4">
				{#if $auth.isAuthenticated}
					<a href={resolve('/user')} class="text-sm text-slate-400">
						{$auth.user?.display_name || $auth.user?.email}
					</a>
					<button
						onclick={handleLogout}
						class="text-sm text-slate-400 transition hover:text-slate-50"
					>
						Logout
					</button>
				{:else}
					<a
						href={resolve('/login')}
						class="text-sm text-indigo-400 transition hover:text-indigo-300"
					>
						Login
					</a>
				{/if}
			</div>
		</div>
	</nav>
{/if}

{@render children()}
