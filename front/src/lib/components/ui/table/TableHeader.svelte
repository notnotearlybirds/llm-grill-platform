<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	type Props = HTMLAttributes<HTMLTableSectionElement>;
	let { class: className = '', ...rest }: Props = $props();
</script>

<thead class={cn('[&_tr]:border-b', className)} {...rest} />
