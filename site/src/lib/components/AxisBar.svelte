<script lang="ts">
	import { SELECTABLE_METRICS, CONCURRENCY_LEVELS } from '$lib/metrics';
	import type { ConcurrencyLevel } from '$lib/types';

	let {
		xKey,
		yKey,
		concurrency,
		onX,
		onY,
		onConcurrency
	}: {
		xKey: string;
		yKey: string;
		concurrency: ConcurrencyLevel;
		onX: (k: string) => void;
		onY: (k: string) => void;
		onConcurrency: (c: ConcurrencyLevel) => void;
	} = $props();

	const levels: ConcurrencyLevel[] = ['agg', ...CONCURRENCY_LEVELS];
</script>

<section class="axes">
	<label class="axis-select">
		<span class="axis-label">X</span>
		<select value={xKey} onchange={(e) => onX(e.currentTarget.value)}>
			{#each SELECTABLE_METRICS as m (m.key)}
				<option value={m.key}>{m.label}</option>
			{/each}
		</select>
		<svg width="10" height="10" viewBox="0 0 10 10" class="axis-chev"
			><path d="M2 4l3 3 3-3" stroke="currentColor" fill="none" stroke-width="1.2" /></svg
		>
	</label>

	<label class="axis-select">
		<span class="axis-label">Y</span>
		<select value={yKey} onchange={(e) => onY(e.currentTarget.value)}>
			{#each SELECTABLE_METRICS as m (m.key)}
				<option value={m.key}>{m.label}</option>
			{/each}
		</select>
		<svg width="10" height="10" viewBox="0 0 10 10" class="axis-chev"
			><path d="M2 4l3 3 3-3" stroke="currentColor" fill="none" stroke-width="1.2" /></svg
		>
	</label>

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

	<div class="encoding">
		<span class="enc-item">
			<span class="enc-swatch">
				<span class="enc-circle sm"></span>
				<span class="enc-circle md"></span>
				<span class="enc-circle lg"></span>
			</span>
			<span class="enc-label">size = requests</span>
		</span>
		<span class="enc-item">
			<span class="enc-gradient"></span>
			<span class="enc-label">color = success</span>
		</span>
	</div>
</section>
