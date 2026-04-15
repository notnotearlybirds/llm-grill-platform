<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	type Props = HTMLAttributes<HTMLHeadingElement>;
	let { class: className = '', ...rest }: Props = $props();
</script>

<h3 class={cn('text-lg font-semibold leading-none tracking-tight', className)} {...rest} />
