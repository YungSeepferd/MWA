import { c as create_ssr_component, d as add_attribute, a as escape, e as each, v as validate_component, n as null_to_empty } from "../../../../chunks/index3.js";
/* empty css                                                             */import { M as MobileNav } from "../../../../chunks/MobileNav.js";
const css$1 = {
  code: ".scoring-chart.svelte-1te1oqt{display:inline-block;background:white;border-radius:var(--radius-lg);box-shadow:0 1px 3px rgba(0, 0, 0, 0.1)}.chart-canvas.svelte-1te1oqt{display:block;border-radius:var(--radius-lg)}",
  map: null
};
const ScoringChart = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { scores } = $$props;
  let { overallScore } = $$props;
  let { size = "medium" } = $$props;
  let { showLabels = true } = $$props;
  let { showValues = true } = $$props;
  let canvas;
  const sizeConfig = {
    small: {
      width: 200,
      height: 120,
      fontSize: 10,
      padding: 10
    },
    medium: {
      width: 300,
      height: 180,
      fontSize: 12,
      padding: 15
    },
    large: {
      width: 400,
      height: 240,
      fontSize: 14,
      padding: 20
    }
  };
  if ($$props.scores === void 0 && $$bindings.scores && scores !== void 0)
    $$bindings.scores(scores);
  if ($$props.overallScore === void 0 && $$bindings.overallScore && overallScore !== void 0)
    $$bindings.overallScore(overallScore);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.showLabels === void 0 && $$bindings.showLabels && showLabels !== void 0)
    $$bindings.showLabels(showLabels);
  if ($$props.showValues === void 0 && $$bindings.showValues && showValues !== void 0)
    $$bindings.showValues(showValues);
  $$result.css.add(css$1);
  return `<div class="scoring-chart svelte-1te1oqt"><canvas${add_attribute("width", sizeConfig[size].width, 0)}${add_attribute("height", sizeConfig[size].height, 0)} class="chart-canvas svelte-1te1oqt"${add_attribute("this", canvas, 0)}></canvas>
</div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gray-50.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--gray-50)}.bg-primary-100.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--primary-100)}.bg-gray-100.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--gray-100)}.bg-gray-200.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--gray-200)}.bg-primary-500.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--primary-500)}.bg-success-500.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--success-500)}.bg-warning-100.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--warning-100)}.bg-error-100.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:var(--error-100)}.bg-success-100.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{background:color-mix(in srgb, var(--success-500) 20%, transparent)}.text-gray-900.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--gray-900)}.text-gray-600.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--gray-600)}.text-gray-500.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--gray-500)}.text-gray-700.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--gray-700)}.text-primary-800.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--primary-800)}.text-primary-600.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--primary-600)}.text-success-800.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--success-800)}.text-warning-800.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--warning-800)}.text-error-800.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{color:var(--error-800)}.text-2xl.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:var(--font-size-2xl)}.text-xl.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:var(--font-size-xl)}.text-lg.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:var(--font-size-lg)}.text-sm.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:var(--font-size-sm)}.text-xs.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:var(--font-size-xs)}.text-6xl.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-size:3.75rem}.font-bold.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-weight:600}.font-semibold.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-weight:500}.font-medium.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{font-weight:500}.mb-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-bottom:var(--space-2)}.mb-4.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-bottom:var(--space-4)}.mb-6.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-bottom:var(--space-6)}.py-6.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding-top:var(--space-6);padding-bottom:var(--space-6)}.py-12.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding-top:3rem;padding-bottom:3rem}.px-4.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding-left:var(--space-4);padding-right:var(--space-4)}.p-3.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding:var(--space-3)}.p-4.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding:var(--space-4)}.pb-20.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding-bottom:5rem}.rounded-lg.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{border-radius:var(--radius-lg)}.rounded-full.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{border-radius:9999px}.space-y-2.svelte-1b0a1z6>.svelte-1b0a1z6+.svelte-1b0a1z6{margin-top:var(--space-2)}.space-y-3.svelte-1b0a1z6>.svelte-1b0a1z6+.svelte-1b0a1z6{margin-top:var(--space-3)}.gap-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{gap:var(--space-2)}.gap-3.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{gap:var(--space-3)}.gap-4.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{gap:var(--space-4)}.gap-6.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{gap:var(--space-6)}.flex.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{display:flex}.flex-col.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{flex-direction:column}.flex-1.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{flex:1}.flex-wrap.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{flex-wrap:wrap}.items-center.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{align-items:center}.justify-between.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{justify-content:space-between}.justify-center.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{justify-content:center}.w-full.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{width:100%}.w-20.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{width:5rem}.w-8.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{width:2rem}.h-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{height:0.5rem}.text-center.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{text-align:center}.min-h-screen.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{min-height:100vh}.container.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{width:100%;margin:0 auto;padding:0 var(--space-4)}.mx-auto.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-left:auto;margin-right:auto}.grid.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{display:grid}.grid-cols-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{grid-template-columns:repeat(2, 1fr)}.border-t.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{border-top-width:1px}.border-gray-200.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{border-color:var(--gray-200)}.ml-1.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-left:var(--space-1)}.ml-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{margin-left:var(--space-2)}.pt-3.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{padding-top:var(--space-3)}.transition-all.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{transition-property:all}.duration-300.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{transition-duration:300ms}.capitalize.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{text-transform:capitalize}@media(min-width: 768px){.md\\:grid-cols-2.svelte-1b0a1z6.svelte-1b0a1z6.svelte-1b0a1z6{grid-template-columns:repeat(2, 1fr)}}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { data } = $$props;
  if ($$props.data === void 0 && $$bindings.data && data !== void 0)
    $$bindings.data(data);
  $$result.css.add(css);
  return `<div class="min-h-screen bg-gray-50 pb-20 svelte-1b0a1z6"><div class="container mx-auto px-4 py-6 svelte-1b0a1z6">
    <header class="mb-6 svelte-1b0a1z6"><div class="flex items-center gap-4 mb-2 svelte-1b0a1z6"><button class="btn btn-secondary">← Back to Contacts
        </button>
        <h1 class="text-2xl font-bold text-gray-900 svelte-1b0a1z6">Contact Details</h1></div></header>

    ${`${data?.contact ? `
      <div class="grid gap-6 svelte-1b0a1z6">
        <div class="card"><h2 class="text-xl font-semibold mb-4 svelte-1b0a1z6">Contact Information</h2>
          <div class="grid gap-4 md:grid-cols-2 svelte-1b0a1z6"><div><h3 class="font-medium text-gray-900 svelte-1b0a1z6">${escape(data.contact.name)}</h3>
              ${data.contact.position ? `<p class="text-gray-600 svelte-1b0a1z6">${escape(data.contact.position)}</p>` : ``}
              ${data.contact.company_name ? `<p class="text-gray-600 svelte-1b0a1z6">${escape(data.contact.company_name)}</p>` : ``}</div>
            
            <div class="space-y-2 svelte-1b0a1z6">${data.contact.email ? `<div class="svelte-1b0a1z6"><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Email:</span>
                  <p class="text-gray-900 svelte-1b0a1z6">${escape(data.contact.email)}</p></div>` : ``}
              ${data.contact.phone ? `<div class="svelte-1b0a1z6"><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Phone:</span>
                  <p class="text-gray-900 svelte-1b0a1z6">${escape(data.contact.phone)}</p></div>` : ``}</div></div></div>

        
        <div class="card"><h2 class="text-xl font-semibold mb-4 svelte-1b0a1z6">Market Intelligence</h2>
          
          
          <div class="grid gap-4 md:grid-cols-2 mb-4 svelte-1b0a1z6">${data.contact.agency_type ? `<div><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Agency Type:</span>
                <div class="mt-1"><span class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm capitalize svelte-1b0a1z6">${escape(data.contact.agency_type.replace("_", " "))}</span></div></div>` : ``}
            
            ${data.contact.confidence_score ? `<div><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Confidence Score:</span>
                <div class="mt-1 flex items-center gap-2 svelte-1b0a1z6"><div class="w-full bg-gray-200 rounded-full h-2 svelte-1b0a1z6"><div class="bg-success-500 h-2 rounded-full transition-all duration-300 svelte-1b0a1z6"${add_attribute("style", `width: ${data.contact.confidence_score * 100}%`, 0)}></div></div>
                  <span class="text-sm font-medium text-gray-900 svelte-1b0a1z6">${escape(Math.round(data.contact.confidence_score * 100))}%
                  </span></div></div>` : ``}</div>

          
          ${data.contact.market_areas?.length > 0 ? `<div class="mb-4 svelte-1b0a1z6"><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Market Areas:</span>
              <div class="mt-2 flex flex-wrap gap-2 svelte-1b0a1z6">${each(data.contact.market_areas, (area) => {
    return `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm svelte-1b0a1z6">${escape(area.name)}
                    ${area.relevance_score ? `<span class="text-xs text-gray-500 ml-1 svelte-1b0a1z6">(${escape(Math.round(area.relevance_score * 100))}%)
                      </span>` : ``}
                  </span>`;
  })}</div></div>` : ``}

          
          ${data.contact.business_context ? `<div><span class="text-sm font-medium text-gray-500 svelte-1b0a1z6">Business Context:</span>
              <div class="mt-2 grid gap-2 md:grid-cols-2 svelte-1b0a1z6">${data.contact.business_context.company_size ? `<div><span class="text-xs text-gray-500 svelte-1b0a1z6">Company Size:</span>
                    <p class="text-sm capitalize svelte-1b0a1z6">${escape(data.contact.business_context.company_size)}</p></div>` : ``}
                ${data.contact.business_context.portfolio_size ? `<div><span class="text-xs text-gray-500 svelte-1b0a1z6">Portfolio Size:</span>
                    <p class="text-sm svelte-1b0a1z6">${escape(data.contact.business_context.portfolio_size)} properties</p></div>` : ``}
                ${data.contact.business_context.specialization ? `<div><span class="text-xs text-gray-500 svelte-1b0a1z6">Specialization:</span>
                    <p class="text-sm svelte-1b0a1z6">${escape(data.contact.business_context.specialization)}</p></div>` : ``}
                ${data.contact.business_context.years_in_business ? `<div><span class="text-xs text-gray-500 svelte-1b0a1z6">Years in Business:</span>
                    <p class="text-sm svelte-1b0a1z6">${escape(data.contact.business_context.years_in_business)} years</p></div>` : ``}</div></div>` : ``}</div>

        
        ${data.scoring ? `<div class="card"><h2 class="text-xl font-semibold mb-4 svelte-1b0a1z6">Scoring Breakdown</h2>
            <div class="grid gap-6 md:grid-cols-2 svelte-1b0a1z6">
              <div class="flex justify-center svelte-1b0a1z6">${validate_component(ScoringChart, "ScoringChart").$$render(
    $$result,
    {
      scores: data.scoring.breakdown,
      overallScore: data.scoring.overall_score,
      size: "medium",
      showLabels: true,
      showValues: true
    },
    {},
    {}
  )}</div>
              
              
              <div class="space-y-3 svelte-1b0a1z6">${each(Object.entries(data.scoring.breakdown), ([category, score]) => {
    return `<div class="flex items-center justify-between svelte-1b0a1z6"><span class="text-sm font-medium text-gray-700 capitalize svelte-1b0a1z6">${escape(category.replace("_", " "))}:
                    </span>
                    <div class="flex items-center gap-2 svelte-1b0a1z6"><div class="w-20 bg-gray-200 rounded-full h-2 svelte-1b0a1z6"><div class="bg-primary-500 h-2 rounded-full svelte-1b0a1z6"${add_attribute("style", `width: ${score * 100}%`, 0)}></div></div>
                      <span class="text-sm font-medium text-gray-900 w-8 svelte-1b0a1z6">${escape(Math.round(score * 100))}%
                      </span></div>
                  </div>`;
  })}
                
                
                <div class="pt-3 border-t border-gray-200 svelte-1b0a1z6"><div class="flex items-center justify-between svelte-1b0a1z6"><span class="text-lg font-semibold text-gray-900 svelte-1b0a1z6">Overall Score:</span>
                    <span class="text-lg font-bold text-primary-600 svelte-1b0a1z6">${escape(Math.round(data.scoring.overall_score * 100))}%
                    </span></div></div>
                
                
                ${data.scoring.recommendations?.length > 0 ? `<div class="pt-3 border-t border-gray-200 svelte-1b0a1z6"><h3 class="text-sm font-medium text-gray-700 mb-2 svelte-1b0a1z6">Recommendations:</h3>
                    <ul class="space-y-1">${each(data.scoring.recommendations, (recommendation) => {
    return `<li class="text-sm text-gray-600 flex items-start gap-2 svelte-1b0a1z6"><span class="text-primary-500 mt-1">•</span>
                          ${escape(recommendation)}
                        </li>`;
  })}</ul></div>` : ``}</div></div></div>` : ``}

        
        ${data.contact.outreach_history?.length > 0 ? `<div class="card"><h2 class="text-xl font-semibold mb-4 svelte-1b0a1z6">Outreach History</h2>
            <div class="space-y-3 svelte-1b0a1z6">${each(data.contact.outreach_history, (outreach) => {
    return `<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg svelte-1b0a1z6"><div><span class="font-medium text-gray-900 capitalize svelte-1b0a1z6">${escape(outreach.method.replace("_", " "))}</span>
                    <span class="text-sm text-gray-500 ml-2 svelte-1b0a1z6">${escape(new Date(outreach.date).toLocaleDateString())}
                    </span></div>
                  <span class="${escape(
      null_to_empty(`px-2 py-1 text-xs rounded-full capitalize ${outreach.outcome === "successful" ? "bg-success-100 text-success-800" : outreach.outcome === "no_response" ? "bg-warning-100 text-warning-800" : "bg-error-100 text-error-800"}`),
      true
    ) + " svelte-1b0a1z6"}">${escape(outreach.outcome.replace("_", " "))}</span>
                </div>`;
  })}</div></div>` : ``}

        
        <div class="card"><h2 class="text-xl font-semibold mb-4 svelte-1b0a1z6">Actions</h2>
          <div class="flex gap-3 svelte-1b0a1z6"><button class="btn btn-primary flex-1 svelte-1b0a1z6">Approve Contact
            </button>
            <button class="btn btn-secondary flex-1 svelte-1b0a1z6">Reject Contact
            </button></div></div></div>` : `
      <div class="card text-center py-12 svelte-1b0a1z6"><div class="text-6xl mb-4 svelte-1b0a1z6">❌</div>
        <h3 class="text-lg font-medium text-gray-900 mb-2 svelte-1b0a1z6">Contact not found</h3>
        <p class="text-gray-600 mb-4 svelte-1b0a1z6">The contact you&#39;re looking for doesn&#39;t exist.</p>
        <button class="btn btn-primary">Back to Contacts</button></div>`}`}</div>

  
  ${validate_component(MobileNav, "MobileNav").$$render($$result, {}, {}, {})}
</div>`;
});
export {
  Page as default
};
