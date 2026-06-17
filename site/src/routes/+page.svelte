<script lang="ts">
	import { onMount } from 'svelte';
	import Header from '$lib/components/Header.svelte';
	import Filters from '$lib/components/Filters.svelte';
	import AxisBar from '$lib/components/AxisBar.svelte';
	import Scatter from '$lib/components/Scatter.svelte';
	import Tooltip from '$lib/components/Tooltip.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import { fetchCatalogs, buildView, type Catalogs } from '$lib/data';
	import { KNOWN_HOMES } from '$lib/config';
	import type { MetricKey } from '$lib/metrics';
	import type { ConcurrencyLevel, ViewRow } from '$lib/types';

	const CATEGORY_ORDER = ['Reasoning', 'MoE', 'Dense', 'Quantized'];
	// Unknown categories sort after the known set (not before, as indexOf -1 would).
	const catRank = (c: string) => {
		const i = CATEGORY_ORDER.indexOf(c);
		return i === -1 ? CATEGORY_ORDER.length : i;
	};

	let catalogs = $state<Catalogs | null>(null);
	let error = $state<string | null>(null);
	let homeUrl = $state<string | null>(null);

	let xKey = $state<MetricKey>('tokens_per_sec');
	let yKey = $state<MetricKey>('ttft_mean');
	let concurrency = $state<ConcurrencyLevel>('agg');
	let trails = $state(false);

	function setTrails(on: boolean) {
		trails = on;
		// Trails put the ramp level on X (the defining axis of a load curve); X/Y stay
		// freely editable via the selectors afterwards.
		if (on) xKey = 'concurrency';
		// Leaving trails: concurrency is a trailsOnly X axis, so reset to a snapshot default.
		else if (xKey === 'concurrency') xKey = 'tokens_per_sec';
	}
	let activeCats = $state(new Set<string>());
	let activeBrands = $state(new Set<string>());
	let activeEngines = $state(new Set<string>());
	let search = $state('');
	let pinned = $state(new Set<string>());
	let hovered = $state<string | null>(null);

	let containerW = $state(0);

	onMount(() => {
		fetchCatalogs()
			.then((c) => (catalogs = c))
			.catch((e) => (error = e instanceof Error ? e.message : String(e)));

		try {
			const stored = localStorage.getItem('home_referrer');
			if (stored) {
				try {
					const storedHost = new URL(stored).hostname;
					const known = KNOWN_HOMES.some(
						(h) => storedHost === h || storedHost.endsWith('.' + h)
					);
					homeUrl = known ? stored : 'https://gireg.fr';
				} catch {
					homeUrl = 'https://gireg.fr';
				}
			} else {
				try {
					const ref = new URL(document.referrer);
					const matched = KNOWN_HOMES.some(
						(h) => ref.hostname === h || ref.hostname.endsWith('.' + h)
					);
					if (matched) {
						localStorage.setItem('home_referrer', ref.origin);
						homeUrl = ref.origin;
					}
				} catch {
					// document.referrer is empty or invalid — no home button
				}
			}
		} catch {
			// localStorage unavailable (disabled storage, strict privacy settings) — fallback to default home
			homeUrl = 'https://gireg.fr';
		}
	});

	const models = $derived(catalogs?.models ?? []);
	const categories = $derived(
		[...new Set(models.flatMap((m) => m.categories))].sort((a, b) => catRank(a) - catRank(b))
	);
	const brands = $derived([...new Set(models.map((m) => m.brand))].sort());

	const view = $derived(
		catalogs ? buildView(catalogs.leaderboard, catalogs.models, concurrency) : []
	);

	function matches(r: ViewRow): boolean {
		if (activeCats.size > 0 && !r.categories.some((c) => activeCats.has(c))) return false;
		if (activeBrands.size > 0 && !activeBrands.has(r.brand)) return false;
		if (activeEngines.size > 0 && !activeEngines.has(r.engine)) return false;
		if (search) {
			const q = search.toLowerCase();
			if (!r.name.toLowerCase().includes(q) && !r.model.toLowerCase().includes(q)) return false;
		}
		return true;
	}

	const filtered = $derived(view.filter(matches));
	const benchedModelIds = $derived(new Set(view.map((r) => r.model)));
	const totalModels = $derived(benchedModelIds.size);

	// Shape encoding: engine index in engines.json → shape index (0=circle, 1=diamond, 2=triangle).
	const engines = $derived(catalogs?.engines ?? []);
	const shapeMap = $derived(new Map(engines.map((e, i) => [e.id, i])));

	// Single chart sizing.
	const CHART_RATIO = 0.42;        // height-to-width aspect ratio
	const CHART_H_MIN = 300;         // floor: enough vertical room to read the scatter
	const CHART_H_MAX_SM = 460;      // cap on narrow viewports (< 900 px wide)
	const CHART_H_MAX_LG = 560;      // cap on wider viewports — taller to preserve visual balance

	const hpad    = $derived(containerW < 900 ? 32 : 48);
	const chartW  = $derived(containerW > 0 ? containerW - hpad : 0);
	const chartHMax = $derived(containerW < 900 ? CHART_H_MAX_SM : CHART_H_MAX_LG);
	const chartH  = $derived(Math.floor(Math.max(CHART_H_MIN, Math.min(chartHMax, chartW * CHART_RATIO))));

	// Tooltip(s): the hovered row wins; otherwise show every pinned row so two models
	// can be compared side by side (single-pin gave no comparison before).
	const tooltipRows = $derived(
		(() => {
			if (hovered) {
				const r = filtered.find((x) => x.id === hovered);
				return r ? [r] : [];
			}
			return [...pinned].map((id) => filtered.find((x) => x.id === id)).filter((r): r is ViewRow => !!r);
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

	// Merge all concurrency levels across scenarios, deduplicated and sorted.
	const concurrencyLevels = $derived(
		[...new Set((catalogs?.scenarios ?? []).flatMap((s) => s.concurrency_levels))].sort(
			(a, b) => a - b
		)
	);

	function toggle(set: Set<string>, v: string): Set<string> {
		const n = new Set(set);
		n.has(v) ? n.delete(v) : n.add(v);
		return n;
	}
	const onToggleCat = (c: string) => (activeCats = toggle(activeCats, c));
	const onToggleBrand = (b: string) => (activeBrands = toggle(activeBrands, b));
	const onToggleEngine = (id: string) => (activeEngines = toggle(activeEngines, id));
	const onPin = (id: string) => (pinned = toggle(pinned, id));
	const concLabel = $derived(concurrency === 'agg' ? 'all' : concurrency);
</script>

<div class="app">
	<Header {totalModels} totalBackends={engines.length} {homeUrl} />

	{#if error}
		<div class="status status-err">failed to load benchmark data — {error}</div>
	{:else if !catalogs}
		<div class="status">loading benchmark data…</div>
	{:else}
		<Filters
			modelsMeta={models}
			{benchedModelIds}
			{categories}
			{brands}
			{activeCats}
			{activeBrands}
			{search}
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
			{trails}
			{concurrencyLevels}
			{engines}
			{activeEngines}
			onX={(k) => (xKey = k)}
			onY={(k) => (yKey = k)}
			onConcurrency={(c) => (concurrency = c)}
			onTrails={setTrails}
			{onToggleEngine}
		/>

		<section class="charts" bind:clientWidth={containerW}>
			{#if chartW > 0}
				<Scatter
					data={filtered}
					{xKey}
					{yKey}
					{trails}
					{shapeMap}
					width={chartW}
					height={chartH}
					{pinned}
					{hovered}
					onHover={(id) => (hovered = id)}
					{onPin}
					label={trails ? 'load curve' : `concurrency = ${concLabel}`}
				/>
			{/if}

			{#if tooltipRows.length}
				<div class="tooltip-wrap">
					{#each tooltipRows as row (row.id)}
						<Tooltip {row} {concurrency} />
					{/each}
				</div>
			{/if}
		</section>

		<Footer {lastRun} {scenarioLabel} />
	{/if}
</div>
