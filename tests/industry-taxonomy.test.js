const assert = require("node:assert/strict");
const taxonomy = require("../assets/industry-taxonomy.js");

const cases = [
  ["Kimi K3 benchmark exceeds Gemini", "ai_models"],
  ["AMD Ryzen 7 desktop CPU review", "pc"],
  ["AMD's next-gen 10-core Medusa Point APU outpaces every x86 mobile chip", "pc"],
  ["New AI server platform uses EPYC processors", "server"],
  ["Oracle data center faces a multibillion-dollar cost surprise", "datacenter"],
  ["TSMC expands CoWoS advanced packaging", "semiconductor"],
  ["GDDR7 memory pricing delays RTX launch", "memory"],
  ["OLED display panel shipments increase", "display"],
  ["Company announces acquisition and appoints a new CEO", "other"],
  ["Nvidia CEO leather jacket charity auction", "other"],
];

assert.deepEqual(
  taxonomy.CATEGORY_DEFS.map(({ id }) => id),
  ["ai_models", "pc", "server", "datacenter", "semiconductor", "memory", "display", "other"]
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
assert.deepEqual(taxonomy.classifyAll({ title: "General technology company update" }), ["other"]);
assert.equal(
  taxonomy.classify({ title: "Ryzen CPU motherboard bundle", summary: "Includes 16GB DDR5 memory" }),
  "pc"
);
assert.deepEqual(
  taxonomy.classifyAll({ title: "Ryzen CPU motherboard bundle", summary: "Includes 16GB DDR5 memory" }),
  ["pc", "memory"]
);

console.log("industry taxonomy: domain-only cases passed");
