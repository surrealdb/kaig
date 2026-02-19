<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { resolve } from '$app/paths';
	import { House, File } from '@lucide/svelte';
</script>

<Sidebar.Root>
	<Sidebar.Header>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Kai G</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					<Sidebar.MenuItem>
						<Sidebar.MenuButton>
							{#snippet child({ props })}
								<a href={resolve('/')} {...props}>
									<House size={24} />
									<span>Home</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
					</Sidebar.MenuItem>
					<Sidebar.MenuItem>
						<Sidebar.MenuButton>
							{#snippet child({ props })}
								<a href={resolve('/files')} {...props}>
									<File size={24} />
									<span>Files</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
					</Sidebar.MenuItem>
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Group />
	</Sidebar.Content>
	<Sidebar.Footer />
</Sidebar.Root>
