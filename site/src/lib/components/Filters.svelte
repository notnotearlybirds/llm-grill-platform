<script lang="ts">
	import type { ModelMeta } from '$lib/types';

	let {
		modelsMeta,
		benchedModelIds,
		categories,
		brands,
		activeCats,
		activeBrands,
		search,
		visibleModels,
		totalModels,
		pinnedCount,
		onToggleCat,
		onToggleBrand,
		onSearch,
		onClearPins
	}: {
		modelsMeta: ModelMeta[];
		benchedModelIds: Set<string>;
		categories: string[];
		brands: string[];
		activeCats: Set<string>;
		activeBrands: Set<string>;
		search: string;
		visibleModels: number;
		totalModels: number;
		pinnedCount: number;
		onToggleCat: (c: string) => void;
		onToggleBrand: (b: string) => void;
		onSearch: (v: string) => void;
		onClearPins: () => void;
	} = $props();

	// Pre-filter by search so pill counts reflect what the current query would match.
	const searchedMeta = $derived(
		search
			? modelsMeta.filter((m) => {
					const q = search.toLowerCase();
					return m.display_name.toLowerCase().includes(q) || m.model.toLowerCase().includes(q);
				})
			: modelsMeta
	);

	// Count distinct benched models — a model on two engines must not count twice.
	const distinctBenched = (rows: ModelMeta[]) =>
		new Set(rows.filter((m) => benchedModelIds.has(m.model)).map((m) => m.model)).size;
	const catCount = (c: string) =>
		distinctBenched(searchedMeta.filter((m) => m.categories.includes(c)));
	const brandCount = (b: string) => distinctBenched(searchedMeta.filter((m) => m.brand === b));
</script>

<section class="filters">
	<div class="filter-row">
		<span class="filter-key">category</span>
		<div class="pills">
			{#each categories.filter((c) => catCount(c) > 0) as c (c)}
				<button class="pill" class:pill-active={activeCats.has(c)} onclick={() => onToggleCat(c)}>
					<span>{c}</span><span class="pill-count">{catCount(c)}</span>
				</button>
			{/each}
		</div>
	</div>
	<div class="filter-row">
		<span class="filter-key">brand</span>
		<div class="pills">
			{#each brands.filter((b) => brandCount(b) > 0) as b (b)}
				<button class="pill" class:pill-active={activeBrands.has(b)} onclick={() => onToggleBrand(b)}>
					<span>{b}</span><span class="pill-count">{brandCount(b)}</span>
				</button>
			{/each}
		</div>
	</div>
	<div class="filter-row">
		<span class="filter-key">search</span>
		<div class="search-box">
			<svg width="12" height="12" viewBox="0 0 12 12" fill="none"
				><circle cx="5" cy="5" r="3.5" stroke="currentColor" stroke-width="1.2" /><path
					d="M7.7 7.7L10 10"
					stroke="currentColor"
					stroke-width="1.2"
					stroke-linecap="round"
				/></svg
			>
			<input
				type="text"
				placeholder="model name or HF id…"
				value={search}
				oninput={(e) => onSearch(e.currentTarget.value)}
			/>
			{#if search}
				<button class="clear-btn" onclick={() => onSearch('')}>×</button>
			{/if}
		</div>
		<div class="filter-status">
			<span class="filter-n">{visibleModels}</span> / {totalModels} models
			{#if pinnedCount > 0}
				<button class="clear-pin" onclick={onClearPins}>clear {pinnedCount} pinned</button>
			{/if}
		</div>
	</div>
</section>
