<script lang="ts">
	import type { PageData } from './$types';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import { shortName } from '$lib/utils';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Palette — cycle through colours for each series
	const PALETTE = [
		'#3b82f6',
		'#22c55e',
		'#f59e0b',
		'#ec4899',
		'#8b5cf6',
		'#14b8a6',
		'#f97316',
		'#06b6d4'
	];

	function seriesColor(i: number): string {
		return PALETTE[i % PALETTE.length] ?? '#3b82f6';
	}

	let ttftSeries = $derived(
		data.history.series.map((s, i) => ({
			key: `${shortName(s.model)} (${s.backend})`,
			color: seriesColor(i),
			points: s.points.map((p) => ({ date: p.date, value: p.ttft_mean }))
		}))
	);

	let tpsSeries = $derived(
		data.history.series.map((s, i) => ({
			key: `${shortName(s.model)} (${s.backend})`,
			color: seriesColor(i),
			points: s.points.map((p) => ({ date: p.date, value: p.tokens_per_sec }))
		}))
	);
</script>

<svelte:head>
	<title>History — llm-grill.fr</title>
</svelte:head>

<h1>Performance History</h1>
<p class="subtitle">Time-series evolution per (model, backend)</p>

<section>
	<h2>TTFT mean over time</h2>
	<TimeSeriesChart series={ttftSeries} title="TTFT mean (ms)" unit=" ms" />
</section>

<section>
	<h2>Tokens/s over time</h2>
	<TimeSeriesChart series={tpsSeries} title="Tokens/s" unit=" tok/s" />
</section>

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
	section {
		margin-bottom: 3rem;
	}
	h2 {
		font-size: 1.1rem;
		margin-bottom: 0.75rem;
		color: #334155;
	}
</style>
