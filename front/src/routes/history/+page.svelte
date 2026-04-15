<script lang="ts">
	import type { PageData } from './$types';
	import TimeSeriesChart from '$lib/components/TimeSeriesChart.svelte';
	import { shortName } from '$lib/utils';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '$lib/components/ui/card';

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

<div class="mb-6">
	<h1 class="text-3xl font-bold tracking-tight">Performance History</h1>
	<p class="text-muted-foreground mt-1 text-sm">Time-series evolution per (model, backend)</p>
</div>

<div class="flex flex-col gap-6">
	<Card>
		<CardHeader>
			<CardTitle>TTFT mean over time</CardTitle>
			<CardDescription>Time to first token (ms) — lower is better</CardDescription>
		</CardHeader>
		<CardContent>
			<TimeSeriesChart series={ttftSeries} title="TTFT mean (ms)" unit=" ms" />
		</CardContent>
	</Card>

	<Card>
		<CardHeader>
			<CardTitle>Tokens/s over time</CardTitle>
			<CardDescription>Throughput — higher is better</CardDescription>
		</CardHeader>
		<CardContent>
			<TimeSeriesChart series={tpsSeries} title="Tokens/s" unit=" tok/s" />
		</CardContent>
	</Card>
</div>
