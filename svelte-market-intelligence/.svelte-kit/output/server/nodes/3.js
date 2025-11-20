import * as universal from '../entries/pages/analytics/_page.js';

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/analytics/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/analytics/+page.js";
export const imports = ["_app/immutable/nodes/3.2edf5331.js","_app/immutable/chunks/index.8f2ca6db.js","_app/immutable/chunks/control.c2cf8273.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/ScoringChart.svelte_svelte_type_style_lang.475579b1.js","_app/immutable/chunks/MobileNav.343364e7.js","_app/immutable/chunks/LineChart.7186ab17.js"];
export const stylesheets = ["_app/immutable/assets/3.77455730.css","_app/immutable/assets/ScoringChart.06e3497c.css","_app/immutable/assets/MobileNav.021b174d.css","_app/immutable/assets/LineChart.7b0ebd2a.css"];
export const fonts = [];
