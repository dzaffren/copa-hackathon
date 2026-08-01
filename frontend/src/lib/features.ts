/**
 * Demo-time toggles. Flip one to re-enable a parked surface — the screen, its
 * routes and its tests stay in the app either way, so only the way in changes.
 */

/** Gates the sidebar's Cross-Workstream Intel entry. The `/intelligence` and
 *  `/intelligence/compare` routes stay mounted regardless, so the screen is
 *  still reachable by direct URL while the nav link is hidden. */
export const SHOW_CROSS_INTEL = false;
