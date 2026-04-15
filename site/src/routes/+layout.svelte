<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="site">
	<header>
		<nav>
			<a href="/" class="brand">🔥 llm-grill.fr</a>
			<a href="/">Leaderboard</a>
			<a href="/history">History</a>
		</nav>
	</header>
	<main>
		{@render children()}
	</main>
	<footer>
		<p>Nightly benchmarks · Open-source models · <a href="https://github.com/llm-grill-nightly/llm-grill-nightly">GitHub</a></p>
	</footer>
</div>

<style>
	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}
	:global(body) {
		margin: 0;
		font-family: system-ui, -apple-system, sans-serif;
		color: #1e293b;
		background: #f8fafc;
	}
	.site {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}
	header {
		background: #1e293b;
		color: white;
		padding: 0 1.5rem;
	}
	nav {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		height: 52px;
	}
	nav a {
		color: #cbd5e1;
		text-decoration: none;
		font-size: 0.9rem;
	}
	nav a:hover {
		color: white;
	}
	.brand {
		font-weight: 700;
		font-size: 1rem !important;
		color: white !important;
		margin-right: 1rem;
	}
	main {
		flex: 1;
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
		padding: 2rem 1.5rem;
	}
	footer {
		background: #1e293b;
		color: #94a3b8;
		text-align: center;
		padding: 1rem;
		font-size: 0.8rem;
	}
	footer a {
		color: #94a3b8;
	}
</style>
