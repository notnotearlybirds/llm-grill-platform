/** Domains that may link to this site and should be used as the home URL. */
export const KNOWN_HOMES = ['gireg.fr', 'karimsayadi.fr'];

/** Fallback home URL when no referrer is detected or stored URL is unrecognised. */
export const DEFAULT_HOME_URL = 'https://gireg.fr';

/** localStorage key used to persist the detected home referrer across page loads. */
export const HOME_REFERRER_KEY = 'home_referrer';

/** Returns true if the given hostname belongs to a known home domain. */
export function isKnownHome(hostname: string): boolean {
	return KNOWN_HOMES.some((h) => hostname === h || hostname.endsWith('.' + h));
}
