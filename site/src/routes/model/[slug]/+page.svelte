<script lang="ts">
	import type { PageData } from './$types';
	import ComparisonChart from '$lib/components/ComparisonChart.svelte';
	import type { ModelRun, Backend } from '$lib/types';
	import { fmtMs, fmtTps, fmtPct, slugToModel } from '$lib/utils';

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

<a href="/" class="back">&larr; Leaderboard</a>

{#if !model}
	<p class="error">Model not found.</p>
{:else}
	<h1>{model.model}</h1>

	<section>
		<h2>Backend comparison — latest run</h2>
		<div class="charts">
			<div>
				<ComparisonChart groups={ttftGroups} title="TTFT mean (ms)" unit=" ms" />
			</div>
			<div>
				<ComparisonChart groups={tpsGroups} title="Tokens/s" unit="" />
			</div>
		</div>
	</section>

	<section>
		<h2>Run history</h2>
		<div class="table-wrapper">
			<table>
				<thead>
					<tr>
						<th>Date</th>
						<th>Backend</th>
						<th>TTFT mean</th>
						<th>TTFT p95</th>
						<th>TPOT mean</th>
						<th>E2E mean</th>
						<th>Tokens/s</th>
						<th>Success</th>
						<th>N</th>
					</tr>
				</thead>
				<tbody>
					{#each sortedRuns as run (`${run.date}-${run.backend}`)}
						<tr>
							<td>{run.date}</td>
							<td><span class="badge badge-{run.backend}">{run.backend}</span></td>
							<td>{fmtMs(run.metrics.ttft_mean)}</td>
							<td>{fmtMs(run.metrics.ttft_p95)}</td>
							<td>{fmtMs(run.metrics.tpot_mean)}</td>
							<td>{fmtMs(run.metrics.e2e_mean)}</td>
							<td>{fmtTps(run.metrics.tokens_per_sec)}</td>
							<td>{fmtPct(run.metrics.success_rate)}</td>
							<td>{run.metrics.n_requests}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<section>
		<h2>Per-conversation breakdown</h2>
		{#each sortedRuns as run (`conv-${run.date}-${run.backend}`)}
			<h3>{run.date} · <span class="badge badge-{run.backend}">{run.backend}</span></h3>
			<div class="table-wrapper">
				<table>
					<thead>
						<tr>
							<th>Conversation</th>
							<th>TTFT mean</th>
							<th>TTFT p95</th>
							<th>TPOT mean</th>
							<th>E2E mean</th>
							<th>Tokens/s</th>
							<th>Success</th>
							<th>N</th>
						</tr>
					</thead>
					<tbody>
						{#each run.conversations as conv (conv.name)}
							<tr>
								<td>{conv.name}</td>
								<td>{fmtMs(conv.metrics.ttft_mean)}</td>
								<td>{fmtMs(conv.metrics.ttft_p95)}</td>
								<td>{fmtMs(conv.metrics.tpot_mean)}</td>
								<td>{fmtMs(conv.metrics.e2e_mean)}</td>
								<td>{fmtTps(conv.metrics.tokens_per_sec)}</td>
								<td>{fmtPct(conv.metrics.success_rate)}</td>
								<td>{conv.metrics.n_requests}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/each}
	</section>
{/if}

<style>
	.back {
		color: #2563eb;
		text-decoration: none;
		font-size: 0.9rem;
	}
	.back:hover {
		text-decoration: underline;
	}
	h1 {
		margin: 0.75rem 0 0.25rem;
		font-size: 1.6rem;
		word-break: break-all;
	}
	h2 {
		font-size: 1.1rem;
		margin: 1.5rem 0 0.75rem;
		color: #334155;
	}
	h3 {
		font-size: 0.95rem;
		margin: 1.25rem 0 0.5rem;
		color: #475569;
	}
	section {
		margin-top: 2rem;
	}
	.charts {
		display: flex;
		gap: 2rem;
		flex-wrap: wrap;
	}
	.table-wrapper {
		overflow-x: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}
	th,
	td {
		padding: 0.45rem 0.7rem;
		border-bottom: 1px solid #e2e8f0;
		text-align: left;
		white-space: nowrap;
	}
	th {
		background: #f8fafc;
		font-weight: 600;
	}
	.badge {
		display: inline-block;
		padding: 0.1rem 0.4rem;
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
	.error {
		color: #dc2626;
		margin-top: 2rem;
	}
</style>
