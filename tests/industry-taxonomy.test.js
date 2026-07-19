const assert = require("node:assert/strict");
const taxonomy = require("../assets/industry-taxonomy.js");

const cases = [
  ["Kimi K3 benchmark exceeds Gemini", "ai_models"],
  ["AMD Ryzen 7 desktop CPU review", "pc"],
  ["New AI server platform uses EPYC processors", "server"],
  ["Oracle data center faces a multibillion-dollar cost surprise", "datacenter"],
  ["TSMC expands CoWoS advanced packaging", "semiconductor"],
  ["GDDR7 memory pricing delays RTX launch", "memory"],
  ["OLED display panel shipments increase", "display"],
  ["Company announces acquisition and appoints a new CEO", "unclassified"],
];

assert.deepEqual(
  taxonomy.CATEGORY_DEFS.map(({ id }) => id),
  ["ai_models", "pc", "server", "datacenter", "semiconductor", "memory", "display"]
);

for (const [title, expected] of cases) {
  assert.equal(taxonomy.classify({ title }), expected, title);
}

assert.deepEqual(
  taxonomy.classifyAll({ title: "Kimi cuts AI networking switch bandwidth with new attention architecture" }),
  ["datacenter", "ai_models"]
);
assert.deepEqual(
  taxonomy.classifyAll({ title: "GDDR7 pricing delays the RTX 5090 launch" }),
  ["memory", "pc"]
);
assert.deepEqual(
  taxonomy.eventLabels({ title: "GDDR7 shortage pushes memory pricing higher" }),
  ["价格变化", "供需变化"]
);
assert.deepEqual(
  taxonomy.eventLabels({ title: "Regulators approve acquisition after antitrust review" }),
  ["并购合作", "政策监管"]
);
assert.equal(taxonomy.classify({ title: "Nvidia CEO leather jacket charity auction" }), "unclassified");
assert.deepEqual(taxonomy.eventLabels({ title: "Nvidia CEO leather jacket charity auction at a $1 million valuation" }), []);
assert.equal(
  taxonomy.classify({ title: "Ryzen CPU motherboard bundle", summary: "Includes 16GB DDR5 memory" }),
  "pc"
);

console.log("industry taxonomy: domain and event cases passed");
