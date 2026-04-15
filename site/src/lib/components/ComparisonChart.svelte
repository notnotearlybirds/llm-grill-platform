<script lang="ts">
	/**
	 * Grouped bar chart comparing two backends for a set of metrics.
	 * Uses a simple SVG approach (LayerCake-inspired) for clarity.
	 */

	interface BarGroup {
		label: string;
		vllm: number | null;
		llamacpp: number | null;
	}

	interface Props {
		groups: BarGroup[];
		title?: string;
		unit?: string;
	}

	let { groups, title = '', unit = '' }: Props = $props();

	const W = 480;
	const H = 260;
	const MARGIN = { top: 30, right: 20, bottom: 50, left: 60 };
	const innerW = W - MARGIN.left - MARGIN.right;
	const innerH = H - MARGIN.top - MARGIN.bottom;

	const BACKENDS = ['vllm', 'llamacpp'] as const;
	const COLORS = { vllm: '#3b82f6', llamacpp: '#22c55e' };

	let maxVal = $derived(
		Math.max(
			1,
			...groups.flatMap((g) =>
				[g.vllm, g.llamacpp].filter((v): v is number => v !== null)
			)
		)
	);

	const groupW = $derived(innerW / groups.length);
	const barW = $derived((groupW - 12) / 2);

	function barX(gi: number, bi: number): number {
		return gi * groupW + bi * (barW + 4);
	}

	function barH(val: number | null): number {
		if (val === null) return 0;
		return (val / maxVal) * innerH;
	}

	function barY(val: number | null): number {
		return innerH - barH(val);
	}

	// Y axis ticks
	const ticks = $derived(
		Array.from({ length: 5 }, (_, i) => {
			const v = (maxVal * (i + 1)) / 5;
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
			<!-- Y axis ticks -->
			{#each ticks as t (t.label)}
				<line x1={0} y1={t.y} x2={innerW} y2={t.y} stroke="#e2e8f0" />
				<text x={-6} y={t.y + 4} text-anchor="end" font-size="11" fill="#64748b">
					{t.label}{unit}
				</text>
			{/each}

			<!-- Bars -->
			{#each groups as g, gi (g.label)}
				{#each BACKENDS as backend, bi (backend)}
					{@const val = g[backend]}
					{@const x = barX(gi, bi)}
					{@const h = barH(val)}
					{@const y = barY(val)}
					<rect
						x={x}
						y={y}
						width={barW}
						height={h}
						fill={COLORS[backend]}
						rx="2"
						opacity="0.85"
					/>
					{#if val !== null && h > 14}
						<text
							x={x + barW / 2}
							y={y + h - 4}
							text-anchor="middle"
							font-size="10"
							fill="white"
						>
							{val.toFixed(0)}
						</text>
					{/if}
				{/each}

				<!-- Group label -->
				<text
					x={gi * groupW + groupW / 2 - barW / 2}
					y={innerH + 16}
					text-anchor="middle"
					font-size="11"
					fill="#334155"
				>
					{g.label}
				</text>
			{/each}

			<!-- Axes -->
			<line x1={0} y1={innerH} x2={innerW} y2={innerH} stroke="#94a3b8" />
			<line x1={0} y1={0} x2={0} y2={innerH} stroke="#94a3b8" />
		</g>

		<!-- Legend -->
		{#each BACKENDS as backend, i (backend)}
			<rect x={MARGIN.left + i * 80} y={H - 18} width={12} height={12} fill={COLORS[backend]} rx="2" />
			<text x={MARGIN.left + i * 80 + 16} y={H - 8} font-size="11" fill="#334155">{backend}</text>
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
