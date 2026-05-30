<script lang="ts">
	let { lastRun, scenarioLabel }: { lastRun: string | null; scenarioLabel: string | null } = $props();
</script>

<footer class="ftr">
	<div class="ftr-l">
		<span>llm-grill.fr</span>
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
