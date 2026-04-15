<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	type Props = HTMLAttributes<HTMLParagraphElement>;
	let { class: className = '', ...rest }: Props = $props();
</script>

<p class={cn('text-sm text-muted-foreground', className)} {...rest} />
