<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { resolve } from '$app/paths';
	import { House, File, FileUp, Folder, ChevronRight, ChevronDown } from '@lucide/svelte';
	import { auth } from '$lib/stores/auth';
	import { getDb } from '$lib/surreal';
	import type { LiveSubscription, RecordId, Surreal } from 'surrealdb';
	import { Table } from 'surrealdb';

	type FileRecord = {
		id: RecordId;
		filename: string;
		path: string;
		content_type: string;
		deleted_at: unknown;
	};

	type TreeNode = {
		name: string;
		isFolder: boolean;
		file?: FileRecord;
		children: TreeNode[];
	};

	type InternalNode = { node: TreeNode; childMap: Record<string, InternalNode> };

	function buildTree(fileList: FileRecord[]): TreeNode[] {
		const rootMap: Record<string, InternalNode> = {};

		for (const file of fileList) {
			const parts = file.path.split('/');
			let currentMap = rootMap;

			for (let i = 0; i < parts.length; i++) {
				const part = parts[i];
				const isLast = i === parts.length - 1;

				if (!currentMap[part]) {
					currentMap[part] = {
						node: { name: part, isFolder: !isLast, file: isLast ? file : undefined, children: [] },
						childMap: {}
					};
				} else if (isLast) {
					currentMap[part].node.file = file;
				} else {
					currentMap[part].node.isFolder = true;
					currentMap[part].node.file = undefined;
				}

				if (!isLast) {
					currentMap = currentMap[part].childMap;
				}
			}
		}

		function toNodes(map: Record<string, InternalNode>): TreeNode[] {
			return Object.values(map)
				.map((entry) => {
					entry.node.children = toNodes(entry.childMap);
					return entry.node;
				})
				.sort((a, b) => {
					if (a.isFolder !== b.isFolder) return a.isFolder ? -1 : 1;
					return a.name.localeCompare(b.name);
				});
		}

		return toNodes(rootMap);
	}

	let files = $state<FileRecord[]>([]);
	let expandedFolders = $state<Set<string>>(new Set());
	let tree = $derived.by(() => {
		const nodes = buildTree(files);
		// Skip a single root folder — show its children directly
		if (nodes.length === 1 && nodes[0].isFolder) return nodes[0].children;
		return nodes;
	});

	function toggleFolder(path: string) {
		const next = new Set(expandedFolders);
		if (next.has(path)) {
			next.delete(path);
		} else {
			next.add(path);
		}
		expandedFolders = next;
	}

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
			if (cancelled) return;

			const [initial] = await db.query<[FileRecord[]]>(
				'SELECT id, filename, path, content_type, created_at FROM file WHERE deleted_at = NONE ORDER BY path ASC'
			);
			if (!cancelled) files = initial ?? [];

			subscription = await db.live<FileRecord>(new Table('file'));
			if (cancelled) {
				await subscription.kill();
				return;
			}

			unsubscribe = subscription.subscribe((message) => {
				console.log(message);
				if (message.action === 'CREATE') {
					const record = message.value as FileRecord;
					if (!record.deleted_at) files = [record, ...files];
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
						files = exists
							? files.map((f) => (String(f.id) === id ? record : f))
							: [record, ...files];
					}
				}
			});
		})();

		return () => {
			cancelled = true;
			if (unsubscribe) unsubscribe();
			if (subscription) subscription.kill().catch(() => {});
		};
	});
</script>

{#snippet treeNode(node: TreeNode, parentPath: string)}
	{@const nodePath = parentPath ? `${parentPath}/${node.name}` : node.name}
	{@const expanded = expandedFolders.has(nodePath)}
	{#if node.isFolder}
		<Sidebar.MenuItem>
			<Sidebar.MenuButton onclick={() => toggleFolder(nodePath)}>
				{#if expanded}
					<ChevronDown size={16} />
				{:else}
					<ChevronRight size={16} />
				{/if}
				<Folder size={16} />
				<span class="truncate">{node.name}</span>
			</Sidebar.MenuButton>
			{#if expanded}
				<Sidebar.MenuSub>
					{#each node.children as item (item.name)}
						<Sidebar.MenuSubItem>
							{@render treeSubNode(item, nodePath)}
						</Sidebar.MenuSubItem>
					{/each}
				</Sidebar.MenuSub>
			{/if}
		</Sidebar.MenuItem>
	{:else if node.file}
		<Sidebar.MenuItem>
			<Sidebar.MenuButton>
				{#snippet child({ props })}
					<a href={resolve(`/files/${node.file!.id.id}`)} {...props}>
						<File size={16} />
						<span class="truncate">{node.name}</span>
					</a>
				{/snippet}
			</Sidebar.MenuButton>
		</Sidebar.MenuItem>
	{/if}
{/snippet}

{#snippet treeSubNode(node: TreeNode, parentPath: string)}
	{@const nodePath = parentPath ? `${parentPath}/${node.name}` : node.name}
	{@const expanded = expandedFolders.has(nodePath)}
	{#if node.isFolder}
		<Sidebar.MenuSubButton onclick={() => toggleFolder(nodePath)}>
			{#if expanded}
				<ChevronDown size={16} />
			{:else}
				<ChevronRight size={16} />
			{/if}
			<Folder size={16} />
			<span class="truncate">{node.name}</span>
		</Sidebar.MenuSubButton>
		{#if expanded}
			<Sidebar.MenuSub>
				{#each node.children as item (item.name)}
					<Sidebar.MenuSubItem>
						{@render treeSubNode(item, nodePath)}
					</Sidebar.MenuSubItem>
				{/each}
			</Sidebar.MenuSub>
		{/if}
	{:else if node.file}
		<Sidebar.MenuSubButton>
			{#snippet child({ props })}
				<a href={resolve(`/files/${node.file!.id.id}`)} {...props}>
					<File size={16} />
					<span class="truncate">{node.name}</span>
				</a>
			{/snippet}
		</Sidebar.MenuSubButton>
	{/if}
{/snippet}

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
						{#each tree as node (node.name)}
							{@render treeNode(node, '')}
						{/each}
					</Sidebar.Menu>
				</Sidebar.GroupContent>
			</Sidebar.Group>
		{/if}
	</Sidebar.Content>
	<Sidebar.Footer />
</Sidebar.Root>
