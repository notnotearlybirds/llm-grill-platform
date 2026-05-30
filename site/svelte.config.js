import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// Fully static SPA: prerender the shell, fetch data at runtime from S3.
		adapter: adapter({ fallback: 'index.html' })
	}
};

export default config;
