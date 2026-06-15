<script lang="ts">
	let { lastRun, scenarioLabel }: { lastRun: string | null; scenarioLabel: string | null } = $props();
	const hostname = window.location.hostname;
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
			<a
				class="ftr-link"
				href="https://github.com/notnotearlybirds/llm-grill-platform/blob/main/scenarios/ramp.yaml"
				target="_blank"
				rel="noopener noreferrer">{scenarioLabel}</a
			>
		{/if}
	</div>
	<div class="ftr-r">
		<span>hover a point for detail</span>
		<span class="ftr-dot">·</span>
		<span>click to pin</span>
	</div>
</footer>
