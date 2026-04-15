// Derived from docs/schemas.md — single source of truth

export type Backend = 'vllm' | 'llamacpp';

export type ConversationName = 'short-qa' | 'coding' | 'multi-turn' | 'long-context';

// --- leaderboard.json ---

export interface LeaderboardEntry {
	model: string; // HuggingFace ID with "/"
	backend: Backend;
	date: string; // YYYY-MM-DD
	ttft_mean: number | null;
	ttft_p95: number | null;
	tpot_mean: number | null;
	e2e_mean: number | null;
	tokens_per_sec: number | null;
	success_rate: number; // [0, 1]
	n_requests: number;
}

export type Leaderboard = LeaderboardEntry[];

// --- models/{slug}.json ---

export interface RunMetrics {
	ttft_mean: number | null;
	ttft_p95: number | null;
	tpot_mean: number | null;
	e2e_mean: number | null;
	tokens_per_sec: number | null;
	success_rate: number;
	n_requests: number;
}

export interface ConversationMetrics {
	name: ConversationName;
	metrics: RunMetrics;
}

export interface ModelRun {
	date: string;
	backend: Backend;
	metrics: RunMetrics;
	conversations: ConversationMetrics[];
}

export interface ModelDetail {
	model: string;
	runs: ModelRun[];
}

// --- history.json ---

export interface HistoryPoint {
	date: string;
	ttft_mean: number | null;
	tokens_per_sec: number | null;
}

export interface HistorySeries {
	model: string;
	backend: Backend;
	points: HistoryPoint[]; // sorted ascending by date
}

export interface History {
	series: HistorySeries[];
}

// --- UI helpers ---

export type SortColumn = keyof Omit<LeaderboardEntry, 'model' | 'backend'>;
export type SortDir = 'asc' | 'desc';
