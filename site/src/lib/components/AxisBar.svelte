<script lang="ts">
	import { METRICS, SELECTABLE_METRICS, type MetricKey } from '$lib/metrics';
	import type { ConcurrencyLevel, EngineMeta } from '$lib/types';

	let {
		xKey,
		yKey,
		concurrency,
		trails,
		concurrencyLevels,
		engines,
		activeEngines,
		onX,
		onY,
		onConcurrency,
		onTrails,
		onToggleEngine
	}: {
		xKey: MetricKey;
		yKey: MetricKey;
		concurrency: ConcurrencyLevel;
		trails: boolean;
		concurrencyLevels: number[];
		engines: EngineMeta[];
		activeEngines: Set<string>;
		onX: (k: MetricKey) => void;
		onY: (k: MetricKey) => void;
		onConcurrency: (c: ConcurrencyLevel) => void;
		onTrails: (on: boolean) => void;
		onToggleEngine: (id: string) => void;
	} = $props();

	const levels: ConcurrencyLevel[] = $derived(['agg', ...concurrencyLevels]);
	// In trails mode the X axis can be the ramp level itself (concurrency), so the
	// trailsOnly metrics become selectable.
	const axisMetrics = $derived(trails ? METRICS : SELECTABLE_METRICS);
</script>

<section class="axes">
	<label class="axis-select">
		<span class="axis-label">X</span>
		<select value={xKey} onchange={(e) => onX(e.currentTarget.value as MetricKey)}>
			{#each axisMetrics as m (m.key)}
				<option value={m.key}>{m.label}</option>
			{/each}
		</select>
		<svg width="10" height="10" viewBox="0 0 10 10" class="axis-chev"
			><path d="M2 4l3 3 3-3" stroke="currentColor" fill="none" stroke-width="1.2" /></svg
		>
	</label>

	<label class="axis-select">
		<span class="axis-label">Y</span>
		<select value={yKey} onchange={(e) => onY(e.currentTarget.value as MetricKey)}>
			{#each axisMetrics as m (m.key)}
				<option value={m.key}>{m.label}</option>
			{/each}
		</select>
		<svg width="10" height="10" viewBox="0 0 10 10" class="axis-chev"
			><path d="M2 4l3 3 3-3" stroke="currentColor" fill="none" stroke-width="1.2" /></svg
		>
	</label>

	<div class="conc-select" title="Snapshot = one ramp level per point; Trails = the load curve per model">
		<span class="axis-label">Mode</span>
		<div class="conc-track">
			<button class="conc-btn" class:conc-on={!trails} onclick={() => onTrails(false)}>snapshot</button>
			<button class="conc-btn" class:conc-on={trails} onclick={() => onTrails(true)}>trails</button>
		</div>
	</div>

	{#if !trails}
		<div class="conc-select" title="Pick the concurrency level to display">
			<span class="axis-label">Concurrency</span>
			<div class="conc-track">
				{#each levels as l (l)}
					<button class="conc-btn" class:conc-on={concurrency === l} onclick={() => onConcurrency(l)}>
						{l === 'agg' ? 'all' : l}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	{#if engines.length > 1}
		<div class="conc-select" title="Filter by inference engine">
			<span class="axis-label">Engine</span>
			<div class="conc-track">
				{#each engines as e (e.id)}
					<button class="conc-btn" class:conc-on={activeEngines.has(e.id)} onclick={() => onToggleEngine(e.id)}>
						{e.label}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<div class="encoding">
		{#if !trails}
			<span class="enc-item">
				<span class="enc-swatch">
					<span class="enc-circle sm"></span>
					<span class="enc-circle md"></span>
					<span class="enc-circle lg"></span>
				</span>
				<span class="enc-label">size = params</span>
			</span>
		{:else}
			<span class="enc-item">
				<span class="enc-range">70%</span>
				<span class="enc-gradient"></span>
				<span class="enc-range">100%</span>
				<span class="enc-label">success</span>
			</span>
		{/if}
		{#each engines as e, i (e.id)}
			<span class="enc-item">
				<svg width="14" height="14" viewBox="-7 -7 14 14" style="flex-shrink:0;display:block">
					{#if i === 1}
						<!-- diamond scaled to circle-equivalent area: half-diagonal = 5 * 1.25 -->
						<polygon points="0,-6.25 6.25,0 0,6.25 -6.25,0" fill="var(--accent)" fill-opacity="0.72" stroke="var(--point-stroke)" stroke-width="1" />
					{:else if i === 2}
						<!-- triangle, circumradius 6.5 to fit viewBox -->
						<polygon points="0,-6.5 5.63,3.25 -5.63,3.25" fill="var(--accent)" fill-opacity="0.72" stroke="var(--point-stroke)" stroke-width="1" />
					{:else}
						<circle r="5" fill="var(--accent)" fill-opacity="0.72" stroke="var(--point-stroke)" stroke-width="1" />
					{/if}
				</svg>
				<span class="enc-label">{e.label}</span>
			</span>
		{/each}
	</div>
</section>
