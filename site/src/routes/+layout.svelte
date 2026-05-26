<script lang="ts">
	import '../app.css';
	// Importing the theme store wires the localStorage <-> data-theme sync.
	import '$lib/theme';

	let { children } = $props();
</script>

{@render children()}
