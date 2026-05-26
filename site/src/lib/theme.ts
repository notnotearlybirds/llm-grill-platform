// Theme store: persists to localStorage and reflects onto <html data-theme>.
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'dark' | 'light';

const KEY = 'llm-grill-theme';

function initial(): Theme {
	if (!browser) return 'dark';
	const saved = localStorage.getItem(KEY);
	return saved === 'light' || saved === 'dark' ? saved : 'dark';
}

export const theme = writable<Theme>(initial());

if (browser) {
	theme.subscribe((value) => {
		document.documentElement.setAttribute('data-theme', value);
		localStorage.setItem(KEY, value);
	});
}

export function toggleTheme(): void {
	theme.update((t) => (t === 'dark' ? 'light' : 'dark'));
}
