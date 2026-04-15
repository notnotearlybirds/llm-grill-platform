import type { PageLoad } from './$types';
import type { Leaderboard } from '$lib/types';

export const prerender = true;

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch('/data/leaderboard.json');
	const leaderboard: Leaderboard = await res.json();
	return { leaderboard };
};
