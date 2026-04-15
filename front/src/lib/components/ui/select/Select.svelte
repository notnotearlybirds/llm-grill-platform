<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLSelectAttributes } from 'svelte/elements';

	type Props = HTMLSelectAttributes;
	let { class: className = '', ...rest }: Props = $props();
</script>

<select
	class={cn(
		'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
		className
	)}
	{...rest}
></select>
