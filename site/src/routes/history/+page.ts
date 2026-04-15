import type { PageLoad } from './$types';
import type { History } from '$lib/types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/data/history.json');
	const history: History = await res.json();
	return { history };
};
