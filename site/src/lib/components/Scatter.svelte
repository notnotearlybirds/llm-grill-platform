<script lang="ts">
	import { flattenPoint, perConcurrency } from '$lib/data';
	import { METRICS, formatTick, type MetricKey } from '$lib/metrics';
	import { paddedDomain, linear, ticksFor, colorScale, radius } from '$lib/scales';
	import type { ViewRow } from '$lib/types';

	let {
		data,
		xKey,
		yKey,
		sizeKey = 'params_b',
		width,
		height,
		pinned,
		hovered,
		onHover,
		onPin,
		showGrid = true,
		label = '',
		trails = false,
		sharedSizeMin,
		sharedSizeMax,
		sharedXDomain,
		shapeMap
	}: {
		data: ViewRow[];
		xKey: MetricKey;
		yKey: MetricKey;
		sizeKey?: MetricKey;
		width: number;
		height: number;
		pinned: Set<string>;
		hovered: string | null;
		onHover: (id: string | null) => void;
		onPin: (id: string) => void;
		showGrid?: boolean;
		label?: string;
		trails?: boolean;
		sharedSizeMin?: number;
		sharedSizeMax?: number;
		sharedXDomain?: [number, number];
		/** engine id → shape index: 0 = circle, 1 = diamond, 2 = triangle */
		shapeMap?: Map<string, number>;
	} = $props();

	const padding = { top: 14, right: 18, bottom: 38, left: 52 };
	const iw = $derived(width - padding.left - padding.right);
	const ih = $derived(height - padding.top - padding.bottom);

	const val = (d: ViewRow, key: MetricKey): number => d[key];

	const xMetric = $derived(METRICS.find((m) => m.key === xKey));
	const yMetric = $derived(METRICS.find((m) => m.key === yKey));

	// Points feeding the domain (include trail points when trails are on).
	const allPoints = $derived(
		(() => {
			const out: { x: number; y: number; s?: number }[] = data.map((d) => ({
				x: val(d, xKey),
				y: val(d, yKey),
				s: val(d, sizeKey)
			}));
			if (trails) {
				for (const d of data) {
					for (const pc of perConcurrency(d._row)) {
						const m = flattenPoint(pc) as Record<string, number>;
						out.push({ x: m[xKey], y: m[yKey] });
					}
				}
			}
			return out;
		})()
	);

	const xDomain = $derived(sharedXDomain ?? paddedDomain(allPoints.map((p) => p.x)));
	const yDomain = $derived(paddedDomain(allPoints.map((p) => p.y)));
	const sizes = $derived(allPoints.map((p) => p.s).filter((s): s is number => s !== undefined));
	const sMin = $derived(sharedSizeMin ?? (sizes.length ? Math.min(...sizes) : 1));
	const sMax = $derived(sharedSizeMax ?? (sizes.length ? Math.max(...sizes) : 1));

	const xScale = $derived(linear(xDomain, [padding.left, padding.left + iw]));
	const yScale = $derived(linear(yDomain, [padding.top + ih, padding.top]));
	const xTicks = $derived(ticksFor(xDomain, 5));
	const yTicks = $derived(ticksFor(yDomain, 5));

	// Skip points whose chosen axes are missing/non-finite (e.g. old leaderboard
	// rows lacking a metric) so we never emit NaN SVG coordinates.
	const points = $derived(
		data.filter(
			(d) =>
				Number.isFinite(val(d, xKey)) && Number.isFinite(val(d, yKey))
		)
	);

	// Nothing to draw: no rows, or rows whose chosen axes are all unplottable
	// (e.g. legacy leaderboard rows missing the selected metric). In trails mode
	// the curve points carry the chart, so fall back to the full point set.
	const noMarks = $derived(trails ? allPoints.length === 0 : points.length === 0);

	const r = (d: ViewRow) => radius(val(d, sizeKey), sMin, sMax);
	const isActive = (id: string) => hovered === id || pinned.has(id);
	const isDim = (id: string) => (pinned.size > 0 || hovered != null) && !isActive(id);

	// Precompute screen-space trail geometry once per row (path + points), instead
	// of recomputing it for the path, every circle, and the label on each render.
	// Filters out per-concurrency points whose selected axes are non-finite so NaN
	// coordinates never reach the SVG.
	const trailData = $derived(
		trails
			? data
					.map((d) => {
						const pts = perConcurrency(d._row)
							.map((pc) => {
								const m = flattenPoint(pc) as Record<string, number>;
								return [xScale(m[xKey]), yScale(m[yKey])] as [number, number];
							})
							.filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
						const path = pts
							.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`)
							.join(' ');
						return { d, pts, path };
					})
					.filter(({ pts }) => pts.length > 0)
			: []
	);

	// Active trail rendered last so it sits on top of inactive ones.
	const sortedTrailData = $derived(
		[...trailData].sort((a, b) => (isActive(a.d.id) ? 1 : 0) - (isActive(b.d.id) ? 1 : 0))
	);

	// Keyboard equivalent of click-to-pin, so the chart is reachable without a mouse.
	function onKey(e: KeyboardEvent, id: string) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			onPin(id);
		}
	}
</script>

{#if noMarks}
	<div class="status" style="width:{width}px;height:{height}px">no runs for this view yet</div>
{:else}
	<svg {width} {height} style="display:block">
	<text x={padding.left} y={padding.top - 2} fill="var(--text-3)" font-size="10" font-family="var(--mono)">{label}</text>

	{#if showGrid}
		{#each yTicks as t, i (i)}
			<line x1={padding.left} x2={width - padding.right} y1={yScale(t)} y2={yScale(t)} stroke="var(--grid)" />
		{/each}
		{#each xTicks as t, i (i)}
			<line y1={padding.top} y2={height - padding.bottom} x1={xScale(t)} x2={xScale(t)} stroke="var(--grid)" />
		{/each}
	{/if}

	{#each yTicks as t, i (i)}
		<text x={padding.left - 8} y={yScale(t) + 3} fill="var(--text-3)" font-size="10" font-family="var(--mono)" text-anchor="end">{formatTick(t, yKey)}</text>
	{/each}
	{#each xTicks as t, i (i)}
		<text x={xScale(t)} y={height - padding.bottom + 14} fill="var(--text-3)" font-size="10" font-family="var(--mono)" text-anchor="middle">{formatTick(t, xKey)}</text>
	{/each}

	<line x1={padding.left} x2={padding.left} y1={padding.top} y2={height - padding.bottom} stroke="var(--axis)" />
	<line x1={padding.left} x2={width - padding.right} y1={height - padding.bottom} y2={height - padding.bottom} stroke="var(--axis)" />

	<text x={padding.left + iw / 2} y={height - 6} fill="var(--text-2)" font-size="11" text-anchor="middle">
		{xMetric?.label}
		{#if xMetric?.unit}<tspan fill="var(--text-4)" font-family="var(--mono)" font-size="10">({xMetric.unit})</tspan>{/if}
	</text>
	<text transform={`rotate(-90 14 ${padding.top + ih / 2})`} x={14} y={padding.top + ih / 2} fill="var(--text-2)" font-size="11" text-anchor="middle">
		{yMetric?.label}
		{#if yMetric?.unit}<tspan fill="var(--text-4)" font-family="var(--mono)" font-size="10">({yMetric.unit})</tspan>{/if}
	</text>

	{#if trails}
		<g>
			{#each sortedTrailData as { d, pts, path } (d.id)}
				<g
					style="opacity:{isDim(d.id) ? 0.06 : isActive(d.id) ? 1 : 0.35};transition:opacity 120ms;cursor:pointer"
					role="button"
					tabindex="0"
					aria-label={d.name}
					onmouseenter={() => onHover(d.id)}
					onmouseleave={() => onHover(null)}
					onfocus={() => onHover(d.id)}
					onblur={() => onHover(null)}
					onclick={() => onPin(d.id)}
					onkeydown={(e) => onKey(e, d.id)}
				>
					<title>{d.name}</title>
					<!-- Invisible wide stroke gives the thin curve a usable hit area. -->
					<path d={path} fill="none" stroke="transparent" stroke-width="12" />
					<path d={path} fill="none" stroke={colorScale(d.success_rate)} stroke-width={isActive(d.id) ? 1.6 : 0.8} stroke-opacity="0.7" />
					{#each pts as p, i (i)}
						<circle cx={p[0]} cy={p[1]} r={isActive(d.id) ? 2.4 : 1.6} fill={colorScale(d.success_rate)} opacity="0.85" />
					{/each}
				</g>
			{/each}
		</g>
	{:else}
	<g>
		{#each points as d (d.id)}
			{@const px = xScale(val(d, xKey))}
			{@const py = yScale(val(d, yKey))}
			{@const pr = r(d)}
			{@const shape = shapeMap?.get(d.engine) ?? 0}
			{@const active = isActive(d.id)}
			<g
				style="opacity:{isDim(d.id) ? 0.18 : 1};transition:opacity 120ms ease;cursor:pointer"
				role="button"
				tabindex="0"
				aria-label={d.name}
				onmouseenter={() => onHover(d.id)}
				onmouseleave={() => onHover(null)}
				onfocus={() => onHover(d.id)}
				onblur={() => onHover(null)}
				onclick={() => onPin(d.id)}
				onkeydown={(e) => onKey(e, d.id)}
			>
				<title>{d.name}</title>
				{#if shape === 1}
					{@const dp = pr * 1.25}
					<polygon
						points="{px},{py - dp} {px + dp},{py} {px},{py + dp} {px - dp},{py}"
						fill="var(--accent)"
						fill-opacity={active ? 0.95 : 0.72}
						stroke={active ? 'var(--text)' : 'var(--point-stroke)'}
						stroke-width={active ? 1.5 : 1}
						style="transition:fill-opacity 120ms,stroke 120ms"
					/>
				{:else if shape === 2}
					{@const tp = pr * 1.56}
					<polygon
						points="{px},{py - tp} {px + tp * 0.866},{py + tp * 0.5} {px - tp * 0.866},{py + tp * 0.5}"
						fill="var(--accent)"
						fill-opacity={active ? 0.95 : 0.72}
						stroke={active ? 'var(--text)' : 'var(--point-stroke)'}
						stroke-width={active ? 1.5 : 1}
						style="transition:fill-opacity 120ms,stroke 120ms"
					/>
				{:else}
					<circle
						cx={px}
						cy={py}
						r={pr}
						fill="var(--accent)"
						fill-opacity={active ? 0.95 : 0.72}
						stroke={active ? 'var(--text)' : 'var(--point-stroke)'}
						stroke-width={active ? 1.5 : 1}
						style="transition:fill-opacity 120ms,stroke 120ms"
					/>
				{/if}
				{#if active}
					<text x={px + pr + 6} y={py + 3} fill="var(--text)" font-size="10.5" font-family="var(--mono)" style="pointer-events:none">{d.name}</text>
				{/if}
			</g>
		{/each}
	</g>
	{/if}
	</svg>
{/if}

<style>
	/* Remove the browser's default rectangular focus ring on SVG interactive elements.
	   Keyboard users still get the model highlight + label via onfocus/onkeydown. */
	circle:focus,
	g:focus {
		outline: none;
	}
</style>
