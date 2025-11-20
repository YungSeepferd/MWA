import * as universal from '../entries/pages/search/new/_page.js';

export const index = 7;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/search/new/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/search/new/+page.js";
export const imports = ["_app/immutable/nodes/7.1a1ed11c.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/parse.492575b6.js","_app/immutable/chunks/singletons.71d606f7.js","_app/immutable/chunks/index.25c19884.js","_app/immutable/chunks/navigation.e2e23cce.js"];
export const stylesheets = ["_app/immutable/assets/7.c500ef82.css"];
export const fonts = [];
