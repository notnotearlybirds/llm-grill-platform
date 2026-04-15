import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

/** Graceful null/undefined metric renderer */
export function formatMetric(value: number | null | undefined): string {
	if (value === null || value === undefined) return '—';
	return String(value);
}

/**
 * Format a number or null as a string with optional unit.
 * Null renders as an em-dash.
 */
export function fmt(value: number | null, decimals = 1, unit = ''): string {
	if (value === null) return '—';
	return `${value.toFixed(decimals)}${unit}`;
}

export function fmtMs(value: number | null): string {
	return fmt(value, 0, ' ms');
}

export function fmtTps(value: number | null): string {
	return fmt(value, 1, ' tok/s');
}

export function fmtPct(value: number): string {
	return `${(value * 100).toFixed(1)}%`;
}

/** Convert HF model ID to URL slug: "/" → "--" */
export function modelToSlug(model: string): string {
	return model.replace(/\//g, '--');
}

/** Convert slug back to HF model ID */
export function slugToModel(slug: string): string {
	return slug.replace(/--/g, '/');
}

/** Short display name: last component of HF ID */
export function shortName(model: string): string {
	const parts = model.split('/');
	return parts[parts.length - 1] ?? model;
}
