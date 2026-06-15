<script lang="ts">
	let { totalModels, engines = [] }: {
		totalModels: number;
		engines?: { label: string; gpu: string }[];
	} = $props();

	const homeUrl = 'https://gireg.fr';
</script>

<header class="hdr">
	<div class="hdr-l">
		<div class="logo">
			<svg class="logo-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
					<path d="M2 8C2 3.5 14 3.5 14 8"/>
					<line x1="1" y1="8" x2="15" y2="8"/>
					<line x1="5" y1="9" x2="3" y2="15"/>
					<line x1="11" y1="9" x2="13" y2="15"/>
					<line x1="3.5" y1="13" x2="12.5" y2="13"/>
				</svg>
			<span class="logo-text">llm-grill</span>
			<span class="logo-dot">·</span>
			<span class="logo-sub">benchmark</span>
		</div>
	</div>
	<div class="hdr-r">
		<div class="stat"><span class="stat-n">{totalModels}</span><span class="stat-l">models</span></div>
		<div class="stat"><span class="stat-n">{engines.length}</span><span class="stat-l">backends</span></div>
		{#each engines as e (e.label)}
			{#if e.gpu}
				<div class="stat"><span class="stat-n">{e.gpu}</span><span class="stat-l">{e.label}</span></div>
			{/if}
		{/each}
		<a class="gh-link home-link" href={homeUrl} title="home" aria-label="home">
			<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
				<path d="M1 7L7 1l6 6" />
				<path d="M2.5 5.5V13h3.5V9h2v4h3.5V5.5" />
			</svg>
		</a>
		<a class="gh-link" title="github" href="https://github.com/notnotearlybirds/llm-grill-platform" aria-label="GitHub" target="_blank" rel="noopener noreferrer">
			<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
				><path
					d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2 .37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"
				/></svg
			>
		</a>
	</div>
</header>
