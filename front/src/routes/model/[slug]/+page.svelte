<script lang="ts">
	import type { PageData } from './$types';
	import ComparisonChart from '$lib/components/ComparisonChart.svelte';
	import type { ModelRun, Backend } from '$lib/types';
	import { fmtMs, fmtTps, fmtPct, slugToModel } from '$lib/utils';
	import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import {
		Table, TableHeader, TableBody, TableRow, TableHead, TableCell
	} from '$lib/components/ui/table';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const model = $derived(data.model);
	const modelName = $derived(model ? model.model : slugToModel(data.slug as string));

	// Latest run per backend
	function latestByBackend(runs: ModelRun[]): Map<Backend, ModelRun> {
		const m = new Map<Backend, ModelRun>();
		for (const run of [...runs].sort((a, b) => b.date.localeCompare(a.date))) {
			if (!m.has(run.backend)) m.set(run.backend, run);
		}
		return m;
	}

	const latestRuns = $derived(model ? latestByBackend(model.runs) : new Map<Backend, ModelRun>());

	const ttftGroups = $derived(
		model
			? model.runs
					.flatMap((r) => r.conversations)
					.filter((c, i, arr) => arr.findIndex((x) => x.name === c.name) === i)
					.map((c) => ({
						label: c.name,
						vllm: latestRuns.get('vllm')?.conversations.find((x) => x.name === c.name)?.metrics.ttft_mean ?? null,
						llamacpp: latestRuns.get('llamacpp')?.conversations.find((x) => x.name === c.name)?.metrics.ttft_mean ?? null
					}))
			: []
	);

	const tpsGroups = $derived(
		model
			? model.runs
					.flatMap((r) => r.conversations)
					.filter((c, i, arr) => arr.findIndex((x) => x.name === c.name) === i)
					.map((c) => ({
						label: c.name,
						vllm: latestRuns.get('vllm')?.conversations.find((x) => x.name === c.name)?.metrics.tokens_per_sec ?? null,
						llamacpp: latestRuns.get('llamacpp')?.conversations.find((x) => x.name === c.name)?.metrics.tokens_per_sec ?? null
					}))
			: []
	);

	// All runs sorted descending
	const sortedRuns = $derived(model ? [...model.runs].sort((a, b) => b.date.localeCompare(a.date)) : []);
</script>

<svelte:head>
	<title>{modelName} — llm-grill.fr</title>
</svelte:head>

<div class="mb-6">
	<a href="/" class="text-sm text-blue-600 hover:underline">&larr; Leaderboard</a>
</div>

{#if !model}
	<Card>
		<CardContent class="py-8 text-center text-destructive">
			Model not found.
		</CardContent>
	</Card>
{:else}
	<div class="mb-6">
		<h1 class="text-2xl font-bold tracking-tight break-all">{model.model}</h1>
	</div>

	<div class="flex flex-col gap-6">
		<Card>
			<CardHeader>
				<CardTitle>Backend comparison — latest run</CardTitle>
				<CardDescription>Grouped by conversation type</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="flex flex-wrap gap-8">
					<ComparisonChart groups={ttftGroups} title="TTFT mean (ms)" unit=" ms" />
					<ComparisonChart groups={tpsGroups} title="Tokens/s" unit="" />
				</div>
			</CardContent>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle>Run history</CardTitle>
			</CardHeader>
			<CardContent class="px-0 pt-0">
				<Table>
					<TableHeader>
						<TableRow class="hover:bg-transparent">
							<TableHead>Date</TableHead>
							<TableHead>Backend</TableHead>
							<TableHead>TTFT mean</TableHead>
							<TableHead>TTFT p95</TableHead>
							<TableHead>TPOT mean</TableHead>
							<TableHead>E2E mean</TableHead>
							<TableHead>Tokens/s</TableHead>
							<TableHead>Success</TableHead>
							<TableHead>N</TableHead>
						</TableRow>
					</TableHeader>
					<TableBody>
						{#each sortedRuns as run (`${run.date}-${run.backend}`)}
							<TableRow>
								<TableCell>{run.date}</TableCell>
								<TableCell><Badge variant={run.backend}>{run.backend}</Badge></TableCell>
								<TableCell>{fmtMs(run.metrics.ttft_mean)}</TableCell>
								<TableCell>{fmtMs(run.metrics.ttft_p95)}</TableCell>
								<TableCell>{fmtMs(run.metrics.tpot_mean)}</TableCell>
								<TableCell>{fmtMs(run.metrics.e2e_mean)}</TableCell>
								<TableCell>{fmtTps(run.metrics.tokens_per_sec)}</TableCell>
								<TableCell>{fmtPct(run.metrics.success_rate)}</TableCell>
								<TableCell>{run.metrics.n_requests}</TableCell>
							</TableRow>
						{/each}
					</TableBody>
				</Table>
			</CardContent>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle>Per-conversation breakdown</CardTitle>
			</CardHeader>
			<CardContent class="flex flex-col gap-6 pt-2">
				{#each sortedRuns as run (`conv-${run.date}-${run.backend}`)}
					<div>
						<div class="flex items-center gap-2 mb-2">
							<span class="text-sm font-medium text-muted-foreground">{run.date}</span>
							<Badge variant={run.backend}>{run.backend}</Badge>
						</div>
						<Table>
							<TableHeader>
								<TableRow class="hover:bg-transparent">
									<TableHead>Conversation</TableHead>
									<TableHead>TTFT mean</TableHead>
									<TableHead>TTFT p95</TableHead>
									<TableHead>TPOT mean</TableHead>
									<TableHead>E2E mean</TableHead>
									<TableHead>Tokens/s</TableHead>
									<TableHead>Success</TableHead>
									<TableHead>N</TableHead>
								</TableRow>
							</TableHeader>
							<TableBody>
								{#each run.conversations as conv (conv.name)}
									<TableRow>
										<TableCell class="font-medium">{conv.name}</TableCell>
										<TableCell>{fmtMs(conv.metrics.ttft_mean)}</TableCell>
										<TableCell>{fmtMs(conv.metrics.ttft_p95)}</TableCell>
										<TableCell>{fmtMs(conv.metrics.tpot_mean)}</TableCell>
										<TableCell>{fmtMs(conv.metrics.e2e_mean)}</TableCell>
										<TableCell>{fmtTps(conv.metrics.tokens_per_sec)}</TableCell>
										<TableCell>{fmtPct(conv.metrics.success_rate)}</TableCell>
										<TableCell>{conv.metrics.n_requests}</TableCell>
									</TableRow>
								{/each}
							</TableBody>
						</Table>
					</div>
				{/each}
			</CardContent>
		</Card>
	</div>
{/if}
