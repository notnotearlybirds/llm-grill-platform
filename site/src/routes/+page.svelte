<script lang="ts">
	import type { PageData } from './$types';
	import MetricsTable from '$lib/components/MetricsTable.svelte';
	import type { LeaderboardEntry, Backend } from '$lib/types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Filter state
	let backendFilter = $state<Set<Backend>>(new Set(['vllm', 'llamacpp']));
	let dateFilter = $state('');

	function toggleBackend(b: Backend) {
		const s = new Set(backendFilter);
		if (s.has(b)) {
			s.delete(b);
		} else {
			s.add(b);
		}
		backendFilter = s;
	}

	let filtered = $derived(
		data.leaderboard.filter((e: LeaderboardEntry) => {
			if (!backendFilter.has(e.backend)) return false;
			if (dateFilter && e.date !== dateFilter) return false;
			return true;
		})
	);

	let allDates = $derived(
		[...new Set(data.leaderboard.map((e: LeaderboardEntry) => e.date))].sort().reverse()
	);
</script>

<svelte:head>
	<title>Leaderboard — llm-grill.fr</title>
</svelte:head>

<h1>LLM Benchmark Leaderboard</h1>
<p class="subtitle">Nightly benchmarks · latest run per (model, backend)</p>

<div class="filters">
	<fieldset>
		<legend>Backend</legend>
		{#each ['vllm', 'llamacpp'] as b (b)}
			<label>
				<input
					type="checkbox"
					checked={backendFilter.has(b as Backend)}
					onchange={() => toggleBackend(b as Backend)}
				/>
				{b}
			</label>
		{/each}
	</fieldset>

	<label class="date-filter">
		Date
		<select bind:value={dateFilter}>
			<option value="">All</option>
			{#each allDates as d (d)}
				<option value={d}>{d}</option>
			{/each}
		</select>
	</label>
</div>

<MetricsTable entries={filtered} />

<style>
	h1 {
		margin: 0 0 0.25rem;
		font-size: 1.75rem;
	}
	.subtitle {
		color: #64748b;
		margin: 0 0 1.5rem;
		font-size: 0.9rem;
	}
	.filters {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
	}
	fieldset {
		border: 1px solid #e2e8f0;
		border-radius: 6px;
		padding: 0.35rem 0.75rem;
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	legend {
		font-size: 0.75rem;
		color: #64748b;
		padding: 0 0.25rem;
	}
	label {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.9rem;
		cursor: pointer;
	}
	.date-filter {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		color: #475569;
	}
	select {
		border: 1px solid #e2e8f0;
		border-radius: 4px;
		padding: 0.25rem 0.5rem;
		font-size: 0.85rem;
	}
</style>
