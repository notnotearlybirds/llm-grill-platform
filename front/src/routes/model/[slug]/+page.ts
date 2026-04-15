import type { PageLoad } from './$types';
import type { ModelDetail } from '$lib/types';

export const prerender = 'auto';

export const load: PageLoad = async ({ fetch, params }) => {
	const res = await fetch(`/data/models/${params.slug}.json`);
	if (!res.ok) {
		return { model: null, slug: params.slug };
	}
	const model: ModelDetail = await res.json();
	return { model, slug: params.slug };
};
