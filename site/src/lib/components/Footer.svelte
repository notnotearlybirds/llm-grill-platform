<script lang="ts">
	import { browser } from '$app/environment';
	let { lastRun, scenarioLabel }: { lastRun: string | null; scenarioLabel: string | null } = $props();
	const hostname = browser ? window.location.hostname : 'llm-grill.gireg.fr';
</script>

<footer class="ftr">
	<div class="ftr-l">
		<span>{hostname}</span>
		{#if lastRun}
			<span class="ftr-dot">·</span>
			<span>last run <span class="mono">{lastRun}</span></span>
		{/if}
		{#if scenarioLabel}
			<span class="ftr-dot">·</span>
			<span>{scenarioLabel}</span>
		{/if}
	</div>
	<div class="ftr-r">
		<span>hover a point for detail</span>
		<span class="ftr-dot">·</span>
		<span>click to pin</span>
	</div>
</footer>
