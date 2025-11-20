import * as universal from '../entries/pages/search/_page.js';

export const index = 6;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/search/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/search/+page.js";
export const imports = ["_app/immutable/nodes/6.61dcd5e4.js","_app/immutable/chunks/index.8f2ca6db.js","_app/immutable/chunks/control.c2cf8273.js","_app/immutable/chunks/index.3da97a40.js","_app/immutable/chunks/websocket.66ffcde3.js","_app/immutable/chunks/api.f5325af4.js","_app/immutable/chunks/errorHandler.253b2d9d.js","_app/immutable/chunks/index.25c19884.js"];
export const stylesheets = ["_app/immutable/assets/6.ae5a72ac.css"];
export const fonts = [];
