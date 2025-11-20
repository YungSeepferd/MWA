

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.ba24b398.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/api.f5325af4.js","_app/immutable/chunks/errorHandler.253b2d9d.js"];
export const stylesheets = ["_app/immutable/assets/0.2730a275.css"];
export const fonts = [];
