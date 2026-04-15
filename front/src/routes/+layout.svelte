<script lang="ts">
	import '../app.css';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="min-h-screen flex flex-col bg-background text-foreground">
	<header class="sticky top-0 z-50 border-b border-border bg-primary text-primary-foreground">
		<nav class="max-w-7xl mx-auto px-6 h-14 flex items-center gap-6">
			<a href="/" class="font-bold text-base text-white mr-4">🔥 llm-grill.fr</a>
			<a href="/" class="text-sm text-slate-300 hover:text-white transition-colors no-underline">Leaderboard</a>
			<a href="/history" class="text-sm text-slate-300 hover:text-white transition-colors no-underline">History</a>
		</nav>
	</header>
	<main class="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
		{@render children()}
	</main>
	<footer class="border-t border-border bg-primary text-center py-4 text-sm text-slate-400">
		Nightly benchmarks · Open-source models ·
		<a class="text-slate-400 hover:text-white" href="https://github.com/llm-grill-nightly/llm-grill-nightly">GitHub</a>
	</footer>
</div>
