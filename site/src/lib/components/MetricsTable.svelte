<script lang="ts">
	import type { LeaderboardEntry, SortColumn, SortDir } from '$lib/types';
	import { fmtMs, fmtTps, fmtPct, modelToSlug, shortName } from '$lib/utils';

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

<div class="table-wrapper">
	<table>
		<thead>
			<tr>
				<th>Model</th>
				<th>Backend</th>
				{#each cols as col (col.key)}
					<th>
						<button onclick={() => toggleSort(col.key)}>
							{col.label}{arrow(col.key)}
						</button>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each sorted as entry (entry.model + entry.backend)}
				<tr>
					<td>
						<a href="/model/{modelToSlug(entry.model)}" title={entry.model}>
							{shortName(entry.model)}
						</a>
					</td>
					<td><span class="badge badge-{entry.backend}">{entry.backend}</span></td>
					<td>{entry.date}</td>
					<td>{fmtMs(entry.ttft_mean)}</td>
					<td>{fmtMs(entry.ttft_p95)}</td>
					<td>{fmtMs(entry.tpot_mean)}</td>
					<td>{fmtMs(entry.e2e_mean)}</td>
					<td>{fmtTps(entry.tokens_per_sec)}</td>
					<td>{fmtPct(entry.success_rate)}</td>
					<td>{entry.n_requests}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.table-wrapper {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.9rem;
	}
	th,
	td {
		padding: 0.5rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid #e2e8f0;
		white-space: nowrap;
	}
	th {
		background: #f8fafc;
		font-weight: 600;
	}
	th button {
		background: none;
		border: none;
		cursor: pointer;
		font-weight: 600;
		font-size: 0.9rem;
		padding: 0;
		color: inherit;
	}
	th button:hover {
		color: #2563eb;
	}
	tbody tr:hover {
		background: #f1f5f9;
	}
	a {
		color: #2563eb;
		text-decoration: none;
	}
	a:hover {
		text-decoration: underline;
	}
	.badge {
		display: inline-block;
		padding: 0.15rem 0.45rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	.badge-vllm {
		background: #dbeafe;
		color: #1e40af;
	}
	.badge-llamacpp {
		background: #dcfce7;
		color: #166534;
	}
</style>
