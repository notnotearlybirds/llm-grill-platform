#!/usr/bin/env node
/**
 * build-data.js
 *
 * If ../results/aggregated/leaderboard.json exists, copies all files from
 * ../results/aggregated/ to static/data/.
 * Otherwise copies static/data/fixtures/* to static/data/ (dev fallback).
 *
 * Invoked automatically from `npm run dev` and `npm run build`.
 */

import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const AGGREGATED = join(ROOT, '..', 'results', 'aggregated');
const FIXTURES = join(ROOT, 'static', 'data', 'fixtures');
const DEST = join(ROOT, 'static', 'data');

function ensureDir(dir) {
	if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function copyDir(src, dest) {
	ensureDir(dest);
	for (const entry of readdirSync(src, { withFileTypes: true })) {
		const srcPath = join(src, entry.name);
		const destPath = join(dest, entry.name);
		if (entry.isDirectory()) {
			copyDir(srcPath, destPath);
		} else {
			copyFileSync(srcPath, destPath);
		}
	}
}

const aggregatedLeaderboard = join(AGGREGATED, 'leaderboard.json');

if (existsSync(aggregatedLeaderboard)) {
	console.log('[build-data] Using results/aggregated/ (real data)');
	copyDir(AGGREGATED, DEST);
} else {
	console.log('[build-data] results/aggregated/ not found — using fixtures');
	// Copy each fixture file to static/data/ (excluding the fixtures/ subdir itself)
	for (const entry of readdirSync(FIXTURES, { withFileTypes: true })) {
		const srcPath = join(FIXTURES, entry.name);
		const destPath = join(DEST, entry.name);
		if (entry.isDirectory()) {
			copyDir(srcPath, destPath);
		} else {
			ensureDir(DEST);
			copyFileSync(srcPath, destPath);
		}
	}
}

console.log('[build-data] Done.');
