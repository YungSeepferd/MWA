

export const index = 8;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/test/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/8.f9ffca64.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/errorHandler.253b2d9d.js"];
export const stylesheets = ["_app/immutable/assets/8.751f6cbf.css"];
export const fonts = [];
