<script lang="ts">
	import type { PageData } from './$types';
	import MetricsTable from '$lib/components/MetricsTable.svelte';
	import type { LeaderboardEntry, Backend } from '$lib/types';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '$lib/components/ui/card';
	import { Select } from '$lib/components/ui/select';

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

<div class="mb-6">
	<h1 class="text-3xl font-bold tracking-tight">LLM Benchmark Leaderboard</h1>
	<p class="text-muted-foreground mt-1 text-sm">Nightly benchmarks · latest run per (model, backend)</p>
</div>

<Card>
	<CardHeader class="pb-3">
		<div class="flex flex-wrap items-center gap-4">
			<div class="flex items-center gap-3">
				<span class="text-sm font-medium text-muted-foreground">Backend</span>
				{#each ['vllm', 'llamacpp'] as b (b)}
					<label class="flex items-center gap-1.5 text-sm cursor-pointer select-none">
						<input
							type="checkbox"
							class="rounded border-border"
							checked={backendFilter.has(b as Backend)}
							onchange={() => toggleBackend(b as Backend)}
						/>
						{b}
					</label>
				{/each}
			</div>
			<div class="flex items-center gap-2">
				<span class="text-sm font-medium text-muted-foreground">Date</span>
				<Select bind:value={dateFilter} class="w-36">
					<option value="">All dates</option>
					{#each allDates as d (d)}
						<option value={d}>{d}</option>
					{/each}
				</Select>
			</div>
			<span class="ml-auto text-xs text-muted-foreground">{filtered.length} result{filtered.length === 1 ? '' : 's'}</span>
		</div>
	</CardHeader>
	<CardContent class="pt-0 px-0">
		<MetricsTable entries={filtered} />
	</CardContent>
</Card>
