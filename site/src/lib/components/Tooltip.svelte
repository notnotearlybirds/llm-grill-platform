<script lang="ts">
	import { pointAt, perConcurrency } from '$lib/data';
	import { fmtMs } from '$lib/metrics';
	import { colorScale } from '$lib/scales';
	import type { ConcurrencyLevel, ViewRow } from '$lib/types';

	let { row, concurrency }: { row: ViewRow; concurrency: ConcurrencyLevel } = $props();

	const isAgg = $derived(concurrency === 'agg');
	const pt = $derived(pointAt(row._row, concurrency));

	// Mini sparkline of TTFT vs concurrency (shown in aggregate mode).
	const W = 110;
	const H = 28;
	const PAD = 2;
	const trail = $derived(
		(() => {
			const ttfts = perConcurrency(row._row).map((p) => p.ttft_mean_s);
			if (ttfts.length < 2) return null;
			const min = Math.min(...ttfts);
			const max = Math.max(...ttfts);
			const n = ttfts.length;
			const x = (i: number) => PAD + (i / (n - 1)) * (W - 2 * PAD);
			const y = (v: number) => PAD + (1 - (v - min) / Math.max(max - min, 1e-6)) * (H - 2 * PAD);
			return ttfts.map((v, i) => [x(i), y(v)] as const);
		})()
	);
</script>

<div class="tooltip">
	<div class="tt-head">
		<div class="tt-name">{row.name}</div>
		<div class="tt-meta">
			<span>{row.brand}</span>
			<span class="tt-dot">·</span>
			<span>{row.params_b}B</span>
			{#if row.categories.length}
				<span class="tt-dot">·</span>
				<span>{row.categories.join(', ')}</span>
			{/if}
		</div>
		<div class="tt-meta tt-meta-2">
			<span class="tt-engine tt-engine-{row.engine}">{row.engine}</span>
			<span>{row.hardware.label}</span>
			{#if row.quantization}
				<span class="tt-dot">·</span>
				<span>{row.quantization}</span>
			{/if}
		</div>
	</div>
	<div class="tt-section-h">
		{isAgg ? 'all concurrency levels (weighted)' : `concurrency = ${concurrency}`}
	</div>
	<div class="tt-grid">
		<div><span class="tt-label">TTFT mean</span><span class="tt-v">{fmtMs(pt.ttft_mean_s)}</span></div>
		<div><span class="tt-label">TTFT p95</span><span class="tt-v">{fmtMs(pt.ttft_p95_s)}</span></div>
		<div><span class="tt-label">TPOT mean</span><span class="tt-v">{(pt.tpot_mean_s * 1000).toFixed(1)} ms</span></div>
		<div><span class="tt-label">E2E mean</span><span class="tt-v">{fmtMs(pt.e2e_mean_s)}</span></div>
		<div><span class="tt-label">Per-stream</span><span class="tt-v">{pt.tokens_per_second_mean.toFixed(1)} tok/s</span></div>
		<div><span class="tt-label">Aggregate</span><span class="tt-v">{pt.total_tokens_per_second.toFixed(0)} tok/s</span></div>
		<div><span class="tt-label">Success</span><span class="tt-v">{(pt.success_rate * 100).toFixed(1)}%</span></div>
		<div><span class="tt-label">Requests</span><span class="tt-v">{pt.n_requests.toLocaleString()}</span></div>
	</div>
	{#if isAgg && trail}
		<div class="tt-mini">
			<span class="tt-mini-l">degradation</span>
			<svg width={W} height={H} class="tt-mini-svg">
				<polyline
					fill="none"
					stroke={colorScale(row.success_rate)}
					stroke-width="1.2"
					points={trail.map((p) => p.join(',')).join(' ')}
				/>
				{#each trail as p, i (i)}
					<circle cx={p[0]} cy={p[1]} r="1.6" fill={colorScale(row.success_rate)} />
				{/each}
			</svg>
		</div>
	{/if}
</div>
