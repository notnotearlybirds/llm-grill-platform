<script lang="ts">
	// Self-hosted fonts (no Google Fonts CDN — RGPD + no render-blocking external request).
	import '@fontsource/geist-sans/300.css';
	import '@fontsource/geist-sans/400.css';
	import '@fontsource/geist-sans/500.css';
	import '@fontsource/geist-sans/600.css';
	import '@fontsource/geist-mono/400.css';
	import '@fontsource/geist-mono/500.css';
	import '../app.css';

	let { children } = $props();
</script>

{@render children()}
