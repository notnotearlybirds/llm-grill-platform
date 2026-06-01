// Theme store: reflects onto <html data-theme>. localStorage is written ONLY on
// manual toggle so the OS preference stays in effect until the user explicitly chooses.
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'dark' | 'light';

const KEY = 'llm-grill-theme';

function initial(): Theme {
	if (!browser) return 'light';
	const saved = localStorage.getItem(KEY);
	if (saved === 'light' || saved === 'dark') return saved;
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export const theme = writable<Theme>(initial());

if (browser) {
	// Only update the DOM attribute — do NOT write to localStorage here.
	theme.subscribe((value) => {
		document.documentElement.setAttribute('data-theme', value);
	});

	// Follow OS changes in real-time when no manual preference is saved.
	window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
		if (!localStorage.getItem(KEY)) {
			theme.set(e.matches ? 'dark' : 'light');
		}
	});
}

export function toggleTheme(): void {
	theme.update((t) => {
		const next = t === 'dark' ? 'light' : 'dark';
		if (browser) localStorage.setItem(KEY, next);
		return next;
	});
}
