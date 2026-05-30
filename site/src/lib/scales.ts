// Scale helpers for the scatter. d3-scale gives us robust linear scales + nice
// ticks; the colour/radius encodings are ported verbatim from the mockup.
import { scaleLinear } from 'd3-scale';

/** Padded [min, max] domain from a set of values (8% padding, like the mockup).
 *  Returns a safe unit domain for an empty set so scales never produce NaN. */
export function paddedDomain(values: number[], padFrac = 0.08): [number, number] {
	const finite = values.filter((v) => Number.isFinite(v));
	if (finite.length === 0) return [0, 1];
	const min = Math.min(...finite);
	const max = Math.max(...finite);
	const pad = (max - min) * padFrac || 1;
	return [min - pad, max + pad];
}

export function linear(domain: [number, number], range: [number, number]) {
	return scaleLinear().domain(domain).range(range);
}

export function ticksFor(domain: [number, number], count = 5): number[] {
	return scaleLinear().domain(domain).ticks(count);
}

/** Success-rate colour: red (0.7) → amber → green (1.0), in oklch. */
export function colorScale(v: number): string {
	const t = Math.max(0, Math.min(1, (v - 0.7) / 0.3));
	const hue = 25 + t * 120;
	const lit = 0.65 + t * 0.07;
	const chr = 0.16 + Math.abs(t - 0.5) * 0.06;
	return `oklch(${lit} ${chr} ${hue})`;
}

/** Point radius from a size value (sqrt scale), honouring the point-scale tweak. */
export function radius(v: number, sMin: number, sMax: number, pointScale = 1): number {
	return 3 + Math.sqrt((v - sMin) / Math.max(1, sMax - sMin)) * 14 * pointScale;
}
