<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLThAttributes } from 'svelte/elements';

	type Props = HTMLThAttributes;
	let { class: className = '', ...rest }: Props = $props();
</script>

<th
	class={cn(
		'h-10 px-3 text-left align-middle font-medium text-muted-foreground whitespace-nowrap',
		className
	)}
	{...rest}
/>
