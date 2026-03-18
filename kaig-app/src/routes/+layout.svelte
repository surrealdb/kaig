<script lang="ts">
	import SunIcon from '@lucide/svelte/icons/sun';
	import MoonIcon from '@lucide/svelte/icons/moon';
	import { ModeWatcher, toggleMode } from 'mode-watcher';

	import { Button } from '@/components/ui/button';
	import * as Avatar from '@/components/ui/avatar';

	import favicon from '$lib/assets/favicon.svg';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { auth } from '$lib/stores/auth';

	import './layout.css';

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

<ModeWatcher />

{#if page.url.pathname !== '/login'}
	<div class="fixed top-3 right-3 z-50">
		{#if $auth.isAuthenticated}
			<DropdownMenu.Root>
				<DropdownMenu.Trigger>
					{#snippet child({ props })}
						<Avatar.Root {...props}>
							<Avatar.Fallback>
								{$auth.user?.display_name || $auth.user?.email}
							</Avatar.Fallback>
						</Avatar.Root>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content class="w-56" align="start">
					<DropdownMenu.Label>
						{$auth.user?.display_name || $auth.user?.email}
					</DropdownMenu.Label>
					<DropdownMenu.Group>
						<DropdownMenu.Item onclick={() => goto(resolve('/user'))}>Profile</DropdownMenu.Item>
						<DropdownMenu.Item onclick={handleLogout}>Logout</DropdownMenu.Item>
						<DropdownMenu.Item onclick={toggleMode}>
							<SunIcon
								class="h-[1.2rem] w-[1.2rem] scale-100 rotate-0 !transition-all dark:scale-0 dark:-rotate-90"
							/>
							<MoonIcon
								class="absolute h-[1.2rem] w-[1.2rem] scale-0 rotate-90 !transition-all dark:scale-100 dark:rotate-0"
							/>
							Toggle Mode</DropdownMenu.Item
						>
					</DropdownMenu.Group>
				</DropdownMenu.Content>
			</DropdownMenu.Root>
		{:else}
			<Button href={resolve('/login')}>Login</Button>
		{/if}
	</div>

	<Sidebar.Provider>
		<AppSidebar />
		<Sidebar.Inset>
			<main>
				<Sidebar.Trigger />
				{@render children()}
			</main>
		</Sidebar.Inset>
	</Sidebar.Provider>
{:else}
	{@render children()}
{/if}
