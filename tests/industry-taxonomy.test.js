const assert = require("node:assert/strict");
const taxonomy = require("../assets/industry-taxonomy.js");

const cases = [
  ["Kimi K3 benchmark exceeds Gemini", "ai_models"],
  ["New multimodal large language model paper", "ai_models"],
  ["AMD Ryzen 7 desktop CPU review", "pc_client"],
  ["Budget SSD review for laptops", "pc_client"],
  ["AI server rack adopts liquid cooling", "server_datacenter"],
  ["Kimi reduces KV transfer networking bandwidth", "server_datacenter"],
  ["GDDR7 memory pricing delays RTX launch", "silicon_supply"],
  ["TSMC CoWoS capacity expands", "silicon_supply"],
  ["Company announces acquisition and new CEO", "company_market"],
  ["White House publishes AI regulation agenda", "company_market"],
];

assert.deepEqual(
  taxonomy.CATEGORY_DEFS.map(({ id }) => id),
  ["ai_models", "pc_client", "server_datacenter", "silicon_supply", "company_market"]
);

for (const [title, expected] of cases) {
  assert.equal(taxonomy.classify({ title }), expected, title);
}

console.log(`industry taxonomy: ${cases.length} cases passed`);

assert.deepEqual(
  taxonomy.classifyAll({ title: "Kimi cuts AI networking switch bandwidth with new attention architecture" }),
  ["server_datacenter", "ai_models"]
);
assert.equal(
  taxonomy.classify({ title: "Nvidia CEO leather jacket raises $1 million at charity auction" }),
  "unclassified"
);
assert.equal(taxonomy.classify({ title: "A pleasant weekend update" }), "unclassified");

console.log("industry taxonomy: core and ambiguity cases passed");
