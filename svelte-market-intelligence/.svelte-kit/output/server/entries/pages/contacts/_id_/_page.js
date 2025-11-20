import { e as error } from "../../../../chunks/index.js";
async function load({ fetch, params }) {
  try {
    const contactResponse = await fetch(`/api/v1/contacts/${params.id}`);
    if (!contactResponse.ok) {
      if (contactResponse.status === 404) {
        error(404, "Contact not found");
      }
      throw new Error(`API Error: ${contactResponse.status} ${contactResponse.statusText}`);
    }
    const contact = await contactResponse.json();
    const scoringResponse = await fetch(`/api/v1/contacts/${params.id}/scoring`);
    let scoring = null;
    if (scoringResponse.ok) {
      scoring = await scoringResponse.json();
    }
    return {
      contact,
      scoring
    };
  } catch (err) {
    console.error("Error loading contact details:", err);
    if (err.status === 404) {
      error(404, err.message);
    }
    error(500, "Failed to load contact details");
  }
}
export {
  load
};
