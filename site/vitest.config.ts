import { defineConfig } from 'vitest/config';

// Standalone from vite.config.ts on purpose: the SvelteKit plugin is not needed
// for the pure data-layer units (data.ts uses only relative imports), and pulling
// it in makes vitest try to resolve $app/* and the SvelteKit runtime.
export default defineConfig({
	test: {
		environment: 'node',
		include: ['tests/**/*.test.ts']
	}
});
