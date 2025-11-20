import * as universal from '../entries/pages/contacts/_id_/_page.js';

export const index = 5;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/contacts/_id_/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/contacts/[id]/+page.js";
export const imports = ["_app/immutable/nodes/5.4b912dbe.js","_app/immutable/chunks/index.8f2ca6db.js","_app/immutable/chunks/control.c2cf8273.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/singletons.71d606f7.js","_app/immutable/chunks/index.25c19884.js","_app/immutable/chunks/navigation.e2e23cce.js","_app/immutable/chunks/ScoringChart.svelte_svelte_type_style_lang.475579b1.js","_app/immutable/chunks/MobileNav.343364e7.js"];
export const stylesheets = ["_app/immutable/assets/5.babcf137.css","_app/immutable/assets/ScoringChart.06e3497c.css","_app/immutable/assets/MobileNav.021b174d.css"];
export const fonts = [];
