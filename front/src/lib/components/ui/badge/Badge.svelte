<script lang="ts">
	import { cn } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'vllm' | 'llamacpp';
	}

	let { class: className = '', variant = 'default', ...rest }: Props = $props();

	const variantClasses: Record<string, string> = {
		default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
		secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
		destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
		outline: 'text-foreground',
		vllm: 'border-transparent bg-blue-100 text-blue-800',
		llamacpp: 'border-transparent bg-green-100 text-green-800'
	};
</script>

<div
	class={cn(
		'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
		variantClasses[variant],
		className
	)}
	{...rest}
/>
