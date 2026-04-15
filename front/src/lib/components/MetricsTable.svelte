<script lang="ts">
	import type { LeaderboardEntry, SortColumn, SortDir } from '$lib/types';
	import { fmtMs, fmtTps, fmtPct, modelToSlug, shortName } from '$lib/utils';
	import {
		Table, TableHeader, TableBody, TableRow, TableHead, TableCell
	} from '$lib/components/ui/table';
	import { Badge } from '$lib/components/ui/badge';

	interface Props {
		entries: LeaderboardEntry[];
	}

	let { entries }: Props = $props();

	let sortCol = $state<SortColumn>('ttft_mean');
	let sortDir = $state<SortDir>('asc');

	function toggleSort(col: SortColumn) {
		if (sortCol === col) {
			sortDir = sortDir === 'asc' ? 'desc' : 'asc';
		} else {
			sortCol = col;
			sortDir = 'asc';
		}
	}

	function cmp(a: number | null, b: number | null, dir: SortDir): number {
		if (a === null && b === null) return 0;
		if (a === null) return 1;
		if (b === null) return -1;
		return dir === 'asc' ? a - b : b - a;
	}

	let sorted = $derived(
		[...entries].sort((a, b) => {
			const col = sortCol;
			if (col === 'date') {
				const d = a.date.localeCompare(b.date);
				return sortDir === 'asc' ? d : -d;
			}
			return cmp(
				a[col] as number | null,
				b[col] as number | null,
				sortDir
			);
		})
	);

	function arrow(col: SortColumn): string {
		if (sortCol !== col) return '';
		return sortDir === 'asc' ? ' ▲' : ' ▼';
	}

	const cols: { key: SortColumn; label: string }[] = [
		{ key: 'date', label: 'Date' },
		{ key: 'ttft_mean', label: 'TTFT mean' },
		{ key: 'ttft_p95', label: 'TTFT p95' },
		{ key: 'tpot_mean', label: 'TPOT mean' },
		{ key: 'e2e_mean', label: 'E2E mean' },
		{ key: 'tokens_per_sec', label: 'Tokens/s' },
		{ key: 'success_rate', label: 'Success' },
		{ key: 'n_requests', label: 'N' }
	];
</script>

<Table>
	<TableHeader>
		<TableRow class="hover:bg-transparent">
			<TableHead class="font-semibold text-foreground">Model</TableHead>
			<TableHead class="font-semibold text-foreground">Backend</TableHead>
			{#each cols as col (col.key)}
				<TableHead>
					<button
						onclick={() => toggleSort(col.key)}
						class="font-semibold text-foreground hover:text-blue-600 transition-colors cursor-pointer bg-transparent border-none p-0 text-sm"
					>
						{col.label}{arrow(col.key)}
					</button>
				</TableHead>
			{/each}
		</TableRow>
	</TableHeader>
	<TableBody>
		{#each sorted as entry (entry.model + entry.backend)}
			<TableRow>
				<TableCell>
					<a href="/model/{modelToSlug(entry.model)}" title={entry.model} class="text-blue-600 hover:underline font-medium">
						{shortName(entry.model)}
					</a>
				</TableCell>
				<TableCell>
					<Badge variant={entry.backend}>{entry.backend}</Badge>
				</TableCell>
				<TableCell>{entry.date}</TableCell>
				<TableCell>{fmtMs(entry.ttft_mean)}</TableCell>
				<TableCell>{fmtMs(entry.ttft_p95)}</TableCell>
				<TableCell>{fmtMs(entry.tpot_mean)}</TableCell>
				<TableCell>{fmtMs(entry.e2e_mean)}</TableCell>
				<TableCell>{fmtTps(entry.tokens_per_sec)}</TableCell>
				<TableCell>{fmtPct(entry.success_rate)}</TableCell>
				<TableCell>{entry.n_requests}</TableCell>
			</TableRow>
		{/each}
	</TableBody>
</Table>
