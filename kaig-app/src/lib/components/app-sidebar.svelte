<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { resolve } from '$app/paths';
	import { House, File, FileUp, Folder } from '@lucide/svelte';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, RecordId, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';

	type FileRecord = {
		id: RecordId;
		filename: string;
		path: string;
		is_folder: boolean;
		deleted_at: unknown;
	};

	let files = $state<FileRecord[]>([]);

	$effect(() => {
		const token = $auth.token;
		if (!token) {
			files = [];
			return;
		}

		let cancelled = false;
		let subscription: LiveSubscription | null = null;
		let db: Surreal | null = null;
		let unsubscribe: (() => void) | null = null;

		(async () => {
			db = await getDb(token);
			if (cancelled) {
				await db.close();
				return;
			}

			// Fetch initial file list
			const [initial] = await db.query<[FileRecord[]]>(
				'SELECT id, filename, path, is_folder, created_at FROM file WHERE deleted_at = NONE ORDER BY is_folder DESC, path ASC'
			);
			if (!cancelled) files = initial ?? [];

			// Subscribe to live changes on the files table
			subscription = await db.live<FileRecord>(new Table('file'));
			if (cancelled) {
				await subscription.kill();
				await db.close();
				return;
			}

			unsubscribe = subscription.subscribe((message) => {
				console.log(message);
				if (message.action === 'CREATE') {
					const record = message.value as FileRecord;
					if (!record.deleted_at) {
						files = [record, ...files];
					}
				} else if (message.action === 'DELETE') {
					const id = String(message.recordId);
					files = files.filter((f) => String(f.id) !== id);
				} else if (message.action === 'UPDATE') {
					const record = message.value as FileRecord;
					const id = String(message.recordId);
					if (record.deleted_at) {
						files = files.filter((f) => String(f.id) !== id);
					} else {
						const exists = files.some((f) => String(f.id) === id);
						if (exists) {
							files = files.map((f) => (String(f.id) === id ? record : f));
						} else {
							files = [record, ...files];
						}
					}
				}
			});
		})();

		return () => {
			cancelled = true;
			if (unsubscribe) unsubscribe();
			if (subscription) subscription.kill().catch(() => {});
			if (db) db.close().catch(() => {});
		};
	});
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
									<FileUp size={24} />
									<span>Upload file</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
					</Sidebar.MenuItem>
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Header>
	<Sidebar.Content>
		{#if $auth.isAuthenticated && files.length > 0}
			<Sidebar.Group>
				<Sidebar.GroupLabel>Files</Sidebar.GroupLabel>
				<Sidebar.GroupContent>
					<Sidebar.Menu>
						{#each files as file (file.id)}
							<Sidebar.MenuItem>
								<Sidebar.MenuButton>
									{#snippet child({ props })}
										<a href={resolve(`/files/${file.id.id}`)} {...props}>
											{#if file.is_folder}
												<Folder size={16} />
											{:else}
												<File size={16} />
											{/if}
											<span class="truncate">{file.path}/{file.filename}</span>
										</a>
									{/snippet}
								</Sidebar.MenuButton>
							</Sidebar.MenuItem>
						{/each}
					</Sidebar.Menu>
				</Sidebar.GroupContent>
			</Sidebar.Group>
		{/if}
	</Sidebar.Content>
	<Sidebar.Footer />
</Sidebar.Root>
