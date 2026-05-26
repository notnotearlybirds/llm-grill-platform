<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '$lib/components/Header.svelte';
	import Filters from '$lib/components/Filters.svelte';
	import AxisBar from '$lib/components/AxisBar.svelte';
	import Scatter from '$lib/components/Scatter.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import { fetchCatalogs, buildView, splitByEngine, type Catalogs } from '$lib/data';
	import type { ConcurrencyLevel, ViewRow } from '$lib/types';

	const CATEGORY_ORDER = ['Reasoning', 'MoE', 'Dense', 'Quantized'];

	let catalogs = $state<Catalogs | null>(null);
	let error = $state<string | null>(null);

	let xKey = $state('tokens_per_sec');
	let yKey = $state('ttft_mean');
	let concurrency = $state<ConcurrencyLevel>(8);
	let activeCats = $state(new Set<string>());
	let activeBrands = $state(new Set<string>());
	let search = $state('');
	let pinned = $state(new Set<string>());
	let hovered = $state<string | null>(null);

	let chartW = $state(720);
	let chartH = $state(520);
	let chartsEl = $state<HTMLElement | undefined>(undefined);

	onMount(() => {
		fetchCatalogs()
			.then((c) => (catalogs = c))
			.catch((e) => (error = e instanceof Error ? e.message : String(e)));

		const ro = new ResizeObserver((entries) => {
			for (const e of entries) {
				const w = e.contentRect.width;
				const single = (w - 16) / 2;
				chartW = Math.floor(single);
				chartH = Math.floor(Math.max(360, Math.min(620, single * 0.72)));
			}
		});
		if (chartsEl) ro.observe(chartsEl);
		return () => ro.disconnect();
	});

	const models = $derived(catalogs?.models ?? []);
	const categories = $derived(
		[...new Set(models.flatMap((m) => m.categories))].sort(
			(a, b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b)
		)
	);
	const brands = $derived([...new Set(models.map((m) => m.brand))].sort());

	const view = $derived(
		catalogs ? buildView(catalogs.leaderboard, catalogs.models, concurrency) : []
	);

	function matches(r: ViewRow): boolean {
		if (activeCats.size > 0 && !r.categories.some((c) => activeCats.has(c))) return false;
		if (activeBrands.size > 0 && !activeBrands.has(r.brand)) return false;
		if (search) {
			const q = search.toLowerCase();
			if (!r.name.toLowerCase().includes(q) && !r.model.toLowerCase().includes(q)) return false;
		}
		return true;
	}

	const filtered = $derived(view.filter(matches));
	const byEngine = $derived(splitByEngine(filtered));
	const totalModels = $derived(new Set(models.map((m) => m.model)).size);
	const visibleModels = $derived(new Set(filtered.map((r) => r.model)).size);

	const focused = $derived(
		(() => {
			if (hovered) return filtered.find((r) => r.id === hovered) ?? null;
			if (pinned.size === 1) return filtered.find((r) => r.id === [...pinned][0]) ?? null;
			return null;
		})()
	);

	const lastRun = $derived(
		(() => {
			if (!catalogs?.leaderboard.length) return null;
			const max = catalogs.leaderboard
				.map((r) => r.measured_at)
				.sort()
				.at(-1);
			return max ? max.replace('T', ' ').slice(0, 16) + ' UTC' : null;
		})()
	);
	const scenarioLabel = $derived(catalogs?.scenarios[0]?.name ? `scenario: ${catalogs.scenarios[0].name}` : null);

	function toggle(set: Set<string>, v: string): Set<string> {
		const n = new Set(set);
		n.has(v) ? n.delete(v) : n.add(v);
		return n;
	}
	const onToggleCat = (c: string) => (activeCats = toggle(activeCats, c));
	const onToggleBrand = (b: string) => (activeBrands = toggle(activeBrands, b));
	const onPin = (id: string) => (pinned = toggle(pinned, id));
	const concLabel = $derived(concurrency === 'agg' ? 'all' : concurrency);
</script>

<div class="app">
	<Header {totalModels} />

	{#if error}
		<div class="status status-err">failed to load benchmark data — {error}</div>
	{:else if !catalogs}
		<div class="status">loading benchmark data…</div>
	{:else}
		<Filters
			modelsMeta={models}
			{categories}
			{brands}
			{activeCats}
			{activeBrands}
			{search}
			{visibleModels}
			{totalModels}
			pinnedCount={pinned.size}
			{onToggleCat}
			{onToggleBrand}
			onSearch={(v) => (search = v)}
			onClearPins={() => (pinned = new Set())}
		/>

		<AxisBar
			{xKey}
			{yKey}
			{concurrency}
			onX={(k) => (xKey = k)}
			onY={(k) => (yKey = k)}
			onConcurrency={(c) => (concurrency = c)}
		/>

		<section class="charts" bind:this={chartsEl}>
			<div class="chart-card">
				<div class="chart-head">
					<span class="chart-title">vLLM</span>
					<span class="chart-sub">1×H100 · bf16</span>
					<span class="chart-count">{byEngine.vllm.length} pts</span>
				</div>
				<Scatter
					data={byEngine.vllm}
					{xKey}
					{yKey}
					width={chartW}
					height={chartH}
					{pinned}
					{hovered}
					onHover={(id) => (hovered = id)}
					{onPin}
					label={`vllm · concurrency = ${concLabel}`}
				/>
			</div>
			<div class="chart-card">
				<div class="chart-head">
					<span class="chart-title">llama.cpp</span>
					<span class="chart-sub">1×L40S · Q4_K_M</span>
					<span class="chart-count">{byEngine.llamacpp.length} pts</span>
				</div>
				<Scatter
					data={byEngine.llamacpp}
					{xKey}
					{yKey}
					width={chartW}
					height={chartH}
					{pinned}
					{hovered}
					onHover={(id) => (hovered = id)}
					{onPin}
					label={`llama.cpp · concurrency = ${concLabel}`}
				/>
			</div>

			{#if focused}
				<div class="tooltip-wrap">
					<Tooltip row={focused} {concurrency} />
				</div>
			{/if}
		</section>

		<Footer {lastRun} {scenarioLabel} />
	{/if}
</div>
