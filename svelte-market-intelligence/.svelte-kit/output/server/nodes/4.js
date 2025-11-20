import * as universal from '../entries/pages/contacts/_page.js';

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/contacts/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/contacts/+page.js";
export const imports = ["_app/immutable/nodes/4.61fb69fe.js","_app/immutable/chunks/index.8f2ca6db.js","_app/immutable/chunks/control.c2cf8273.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/index.25c19884.js","_app/immutable/chunks/api.f5325af4.js","_app/immutable/chunks/errorHandler.253b2d9d.js"];
export const stylesheets = ["_app/immutable/assets/4.47a07215.css"];
export const fonts = [];
