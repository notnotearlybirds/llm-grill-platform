// Generates dev fixtures under static/sample/ in the REAL flat S3 format
// (leaderboard.json / models.json / scenarios.json). Deterministic.
// Run: node scripts/gen-sample.mjs
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'static', 'sample');
const LEVELS = [1, 4, 8, 16, 32, 64];

const MODELS = [
	{ model: 'meta-llama/Llama-3.1-8B-Instruct', brand: 'Meta', params_b: 8, categories: ['Dense'] },
	{ model: 'meta-llama/Llama-3.1-70B-Instruct', brand: 'Meta', params_b: 70, categories: ['Dense'] },
	{ model: 'mistralai/Mixtral-8x7B-Instruct', brand: 'Mistral', params_b: 47, categories: ['MoE'] },
	{ model: 'Qwen/Qwen2.5-14B-Instruct', brand: 'Qwen', params_b: 14, categories: ['Dense'] },
	{ model: 'Qwen/QwQ-32B-Preview', brand: 'Qwen', params_b: 32, categories: ['Reasoning'] },
	{ model: 'google/gemma-2-27b-it', brand: 'Google', params_b: 27, categories: ['Dense'] }
];

function seedRand(seed) {
	let s = seed;
	return () => ((s = (s * 9301 + 49297) % 233280), s / 233280);
}

function perConcurrency(meta, engine) {
	const rng = seedRand(
		[...meta.model].reduce((a, c) => a + c.charCodeAt(0), 0) + (engine === 'vllm' ? 17 : 91)
	);
	const p = meta.params_b;
	const isMoE = meta.categories.includes('MoE');
	const active = isMoE ? p * 0.15 : p;
	const backendMul = engine === 'vllm' ? 1 : 4 + rng() * 1.2;
	const hwMul = engine === 'vllm' ? 1 : 0.7;
	const capacity = engine === 'vllm' ? 32 : 4;
	const ttftBase = (0.08 + Math.sqrt(p) * 0.018 + (isMoE ? 0.04 : 0)) * backendMul * hwMul;
	const tpotBase = (0.012 + active * 0.00018) * backendMul * hwMul;
	const out = 109;
	return LEVELS.map((c) => {
		const q = c <= capacity ? 1 + (c - 1) * 0.06 : 1 + ((c - capacity) / capacity) * 0.8 + (c - 1) * 0.06;
		const ttft = ttftBase * q * (0.9 + rng() * 0.2);
		const ttftP95 = ttft * (1.25 + rng() * 0.3);
		const ttftMed = ttft * (0.85 + rng() * 0.1);
		const tpot = tpotBase * (1 + Math.max(0, c - capacity) * 0.015) * (0.95 + rng() * 0.1);
		const tps = (1 / tpot) * (0.92 + rng() * 0.1);
		const e2e = ttft + tpot * out;
		const e2eP95 = ttftP95 + tpot * (1.1 + rng() * 0.15) * out;
		const total = tps * c * (0.85 + rng() * 0.1);
		let fail = 0;
		if (engine === 'llamacpp' && p > 40 && c > 16) fail += 0.05 + rng() * 0.1;
		if (c > 32) fail += rng() * 0.02;
		const success = Math.max(0.5, Math.min(1, 1 - fail));
		const n = Math.round((engine === 'vllm' ? 60 : 32) * (c / 8));
		const f = (x, d) => +x.toFixed(d);
		return {
			concurrency: c,
			n_requests: n,
			success_rate: f(success, 3),
			ttft_mean_s: f(ttft, 4),
			ttft_median_s: f(ttftMed, 4),
			ttft_p95_s: f(ttftP95, 4),
			tpot_mean_s: f(tpot, 5),
			e2e_mean_s: f(e2e, 3),
			e2e_p95_s: f(e2eP95, 3),
			tokens_per_second_mean: f(tps, 2),
			total_tokens_per_second: f(total, 2),
			requests_per_second: f(total / out, 3)
		};
	});
}

function aggregate(pc) {
	const totalReq = pc.reduce((a, p) => a + p.n_requests, 0);
	const wmean = (k) => pc.reduce((a, p) => a + p[k] * p.n_requests, 0) / totalReq;
	const f = (x, d) => +x.toFixed(d);
	return {
		n_requests: totalReq,
		success_rate: f(wmean('success_rate'), 3),
		ttft_mean_s: f(wmean('ttft_mean_s'), 4),
		ttft_median_s: f(wmean('ttft_median_s'), 4),
		ttft_p95_s: f(wmean('ttft_p95_s'), 4),
		tpot_mean_s: f(wmean('tpot_mean_s'), 5),
		e2e_mean_s: f(wmean('e2e_mean_s'), 3),
		e2e_p95_s: f(wmean('e2e_p95_s'), 3),
		tokens_per_second_mean: f(wmean('tokens_per_second_mean'), 2),
		total_tokens_per_second: f(Math.max(...pc.map((p) => p.total_tokens_per_second)), 2),
		requests_per_second: f(wmean('requests_per_second'), 3)
	};
}

const leaderboard = [];
const modelsCatalog = [];
const MEASURED = '2026-05-22T14:22:00+00:00';

function displayName(model) {
	return model
		.split('/')
		.pop()
		.replace(/-(?:Instruct|it|Chat|Preview)$/i, '')
		.replace(/[-_]/g, ' ')
		.trim();
}

for (const meta of MODELS) {
	for (const engine of ['vllm', 'llamacpp']) {
		if (engine === 'llamacpp' && meta.params_b > 70 && !meta.categories.includes('MoE')) continue;
		const pc = perConcurrency(meta, engine);
		const agg = aggregate(pc);
		const gpu = engine === 'vllm' ? 'H100' : 'L40S';
		leaderboard.push({
			model: meta.model,
			engine,
			gpu_type: gpu,
			...agg,
			per_concurrency: pc,
			run_id: `run-${engine}-001`,
			measured_at: MEASURED
		});
		modelsCatalog.push({
			model: meta.model,
			engine,
			display_name: displayName(meta.model),
			brand: meta.brand,
			params_b: meta.params_b,
			quantization: engine === 'llamacpp' ? 'Q4_K_M' : null,
			categories: meta.categories,
			scenario: 'scenarios/ramp.yaml'
		});
	}
}

const scenarios = [
	{
		path: 'scenarios/ramp.yaml',
		name: 'ramp',
		description: 'Ramp load test across concurrency levels.',
		concurrency_levels: LEVELS,
		iterations: 2,
		max_tokens: 256,
		prompt: 'Explain in one paragraph why the sky is blue.'
	}
];

// Ordered engine catalog (mirrors the backend Engine enum / build_engines_catalog).
const engines = [
	{ id: 'vllm', label: 'vLLM' },
	{ id: 'llamacpp', label: 'llama.cpp' }
];

mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, 'leaderboard.json'), JSON.stringify(leaderboard, null, 2));
writeFileSync(join(OUT, 'models.json'), JSON.stringify(modelsCatalog, null, 2));
writeFileSync(join(OUT, 'scenarios.json'), JSON.stringify(scenarios, null, 2));
writeFileSync(join(OUT, 'engines.json'), JSON.stringify(engines, null, 2));
console.log(`wrote ${leaderboard.length} leaderboard rows to ${OUT}`);
