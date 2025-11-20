

export const index = 1;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/error.svelte.js')).default;
export const imports = ["_app/immutable/nodes/1.358899fb.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/singletons.71d606f7.js","_app/immutable/chunks/index.25c19884.js"];
export const stylesheets = [];
export const fonts = [];
