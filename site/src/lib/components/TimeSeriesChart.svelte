<script lang="ts">
	/**
	 * Line chart for time series data.
	 * Each series has a model+backend key and an array of {date, value} points.
	 */

	interface DataPoint {
		date: string;
		value: number | null;
	}

	interface Series {
		key: string; // e.g. "Llama-3.1-8B (vllm)"
		color: string;
		points: DataPoint[];
	}

	interface Props {
		series: Series[];
		title?: string;
		unit?: string;
	}

	let { series, title = '', unit = '' }: Props = $props();

	const W = 560;
	const H = 260;
	const MARGIN = { top: 30, right: 20, bottom: 50, left: 65 };
	const innerW = W - MARGIN.left - MARGIN.right;
	const innerH = H - MARGIN.top - MARGIN.bottom;

	// Collect all dates
	let allDates = $derived(
		[...new Set(series.flatMap((s) => s.points.map((p) => p.date)))].sort()
	);

	let maxVal = $derived(
		Math.max(
			1,
			...series.flatMap((s) =>
				s.points.map((p) => p.value).filter((v): v is number => v !== null)
			)
		)
	);

	function xPos(date: string): number {
		const i = allDates.indexOf(date);
		if (allDates.length < 2) return innerW / 2;
		return (i / (allDates.length - 1)) * innerW;
	}

	function yPos(val: number | null): number {
		if (val === null) return innerH;
		return innerH - (val / maxVal) * innerH;
	}

	function polyline(s: Series): string {
		return s.points
			.filter((p) => p.value !== null)
			.map((p) => `${xPos(p.date)},${yPos(p.value)}`)
			.join(' ');
	}

	const yTicks = $derived(
		Array.from({ length: 4 }, (_, i) => {
			const v = (maxVal * (i + 1)) / 4;
			return { y: innerH - (v / maxVal) * innerH, label: v.toFixed(0) };
		})
	);
</script>

<figure>
	{#if title}
		<figcaption>{title}</figcaption>
	{/if}
	<svg viewBox="0 0 {W} {H}" width={W} height={H} role="img" aria-label={title}>
		<g transform="translate({MARGIN.left},{MARGIN.top})">
			<!-- Grid + Y axis -->
			{#each yTicks as t (t.label)}
				<line x1={0} y1={t.y} x2={innerW} y2={t.y} stroke="#e2e8f0" />
				<text x={-8} y={t.y + 4} text-anchor="end" font-size="11" fill="#64748b">
					{t.label}{unit}
				</text>
			{/each}

			<!-- X axis dates -->
			{#each allDates as date, i (date)}
				<text
					x={xPos(date)}
					y={innerH + 16}
					text-anchor="middle"
					font-size="10"
					fill="#64748b"
				>
					{date.slice(5)}
				</text>
				<line
					x1={xPos(date)}
					y1={0}
					x2={xPos(date)}
					y2={innerH}
					stroke="#f1f5f9"
				/>
			{/each}

			<!-- Lines -->
			{#each series as s (s.key)}
				<polyline
					points={polyline(s)}
					fill="none"
					stroke={s.color}
					stroke-width="2"
					stroke-linejoin="round"
				/>
				<!-- Dots -->
				{#each s.points.filter((p) => p.value !== null) as p (p.date)}
					<circle
						cx={xPos(p.date)}
						cy={yPos(p.value)}
						r="4"
						fill={s.color}
						stroke="white"
						stroke-width="1.5"
					/>
				{/each}
			{/each}

			<!-- Axes -->
			<line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="#94a3b8" />
			<line x1={0} y1={0} x2={0} y2={innerH} stroke="#94a3b8" />
		</g>

		<!-- Legend -->
		{#each series as s, i (s.key)}
			<line
				x1={MARGIN.left}
				y1={H - 20 + i * 0}
				x2={MARGIN.left + 18}
				y2={H - 20 + i * 0}
				stroke={s.color}
				stroke-width="2"
			/>
		{/each}
		{#each series as s, i (s.key)}
			<rect x={10 + i * 140} y={H - 24} width={14} height={3} fill={s.color} />
			<text x={26 + i * 140} y={H - 16} font-size="10" fill="#334155">{s.key}</text>
		{/each}
	</svg>
</figure>

<style>
	figure {
		margin: 0;
	}
	figcaption {
		font-size: 0.9rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		color: #1e293b;
	}
	svg {
		display: block;
		max-width: 100%;
	}
</style>
