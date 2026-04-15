<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLTdAttributes } from 'svelte/elements';

	type Props = HTMLTdAttributes;
	let { class: className = '', ...rest }: Props = $props();
</script>

<td class={cn('px-3 py-2 align-middle whitespace-nowrap', className)} {...rest} />
