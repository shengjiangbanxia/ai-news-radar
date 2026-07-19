(function industryTaxonomyModule(root) {
  "use strict";

  const CATEGORY_DEFS = [
    { id: "ai_models", label: "AI与模型", short: "AI", description: "大模型、Agent、训练、推理、算法、Benchmark与AI平台" },
    { id: "pc_client", label: "PC与终端", short: "PC", description: "Notebook、Desktop、Workstation、CPU、NPU、客户端GPU、显示与外设" },
    { id: "server_datacenter", label: "Server与数据中心", short: "Server", description: "AI Server、加速器、机架、网络、液冷、电力与云基础设施" },
    { id: "silicon_supply", label: "芯片与供应链", short: "供应链", description: "晶圆代工、先进封装、存储、面板、产能、价格与供需" },
    { id: "company_market", label: "公司与市场", short: "市场", description: "企业战略、资本开支、财报、融资并购、政策、组织与竞争格局" },
  ];

  const RULES = {
    ai_models: [
      [6, /\b(?:benchmark|eval|paper|arxiv|dataset|training|fine[- ]?tuning|reasoning|multimodal)\b|基准|论文|数据集|训练|推理|多模态/i],
      [5, /\b(?:llm|large language model|foundation model|ai agent|agentic|transformer|diffusion|rag)\b|大模型|基础模型|智能体/i],
      [4, /\b(?:gpt|claude|gemini|grok|llama|qwen|deepseek|mistral|kimi|glm|gemma)\b/i],
      [2, /\b(?:openai|anthropic|model|inference|attention|token)\b|模型|注意力/i],
    ],
    pc_client: [
      [6, /\b(?:notebook|laptop|desktop|workstation|ai pc|copilot\+ pc|personal computer)\b|笔记本|台式机|工作站|个人电脑/i],
      [5, /\b(?:ryzen|core ultra|snapdragon x|macbook|chromebook|client gpu)\b/i],
      [4, /\b(?:cpu|npu|ssd|motherboard|webcam|headset|keyboard|touchpad|thunderbolt|usb-c|gameboy|handheld)\b|处理器|固态硬盘|掌机|主板|摄像头|耳机|键盘|触控板/i],
      [3, /\b(?:rtx\s?\d{3,4}|radeon|geforce|ssd review|display|audio|monitor)\b|显卡|显示器|音频|评测/i],
    ],
    server_datacenter: [
      [7, /\b(?:data center|datacenter|ai server|server rack|hyperscaler|supercomputer)\b|数据中心|服务器|超级计算机/i],
      [6, /\b(?:nvlink|infiniband|cxl|ai networking|networking switch|optical interconnect|silicon photonics)\b|网络交换机|光互连|硅光/i],
      [5, /\b(?:rack|cluster|liquid cooling|cloud infrastructure|accelerator)\b|机架|集群|液冷|云基础设施|加速器/i],
      [4, /\b(?:bandwidth|ethernet|power infrastructure|gpu cluster|kv[- ]?transfer)\b|带宽|电力基础设施/i],
    ],
    silicon_supply: [
      [8, /\b(?:hbm\d?|dram|nand|gddr\d?|lpddr\d?|ddr\d?|memory chip)\b|内存|存储芯片/i],
      [7, /\b(?:foundry|wafer|cowos|advanced packaging|semiconductor fab)\b|晶圆|代工|先进封装|半导体制造/i],
      [6, /\b(?:tsmc|cxmt|micron|sk hynix|kioxia|asml)\b|台积电|长鑫|美光|镁光|海力士|阿斯麦/i],
      [5, /\b(?:capacity|shortage|supply chain|shipment|inventory)\b|产能|短缺|供应链|出货|库存/i],
      [4, /\b(?:panel price|memory price|chip price|pricing)\b|面板价格|存储价格|芯片价格/i],
    ],
    company_market: [
      [8, /\b(?:capex|earnings|revenue|profit|multibillion[- ]dollar cost|cost surprise)\b|资本开支|财报|营收|利润|成本意外/i],
      [7, /\b(?:funding|raised|ipo|acquisition|acquire|merger|investor|valuation)\b|融资|首次公开募股|收购|并购|投资者|估值/i],
      [7, /\b(?:regulation|policy|antitrust|tariff|sanction|white house|agenda)\b|监管|政策|反垄断|关税|制裁|议程/i],
      [6, /\b(?:ceo|executive|resign|left|joins|layoff|restructur)\b|首席执行官|高管|离职|加入|裁员|重组/i],
      [5, /\b(?:market share|tam|competition|strategy|commercial)\b|市场份额|竞争|战略|商业化/i],
      [3, /\b(?:apple|microsoft|google|meta|oracle|nvidia|amd|intel|qualcomm|broadcom)\b/i],
    ],
  };

  const TIE_ORDER = ["silicon_supply", "server_datacenter", "pc_client", "ai_models", "company_market"];

  function textFor(item) {
    return [
      item?.title,
      item?.title_zh,
      item?.title_en,
      item?.title_original,
      item?.summary,
      item?.summary_zh,
    ].filter(Boolean).join(" ").toLowerCase();
  }

  function classify(item) {
    if (item?.industry_category && CATEGORY_DEFS.some((category) => category.id === item.industry_category)) {
      return item.industry_category;
    }
    const text = textFor(item);
    const scores = Object.fromEntries(CATEGORY_DEFS.map((category) => [category.id, 0]));
    Object.entries(RULES).forEach(([category, rules]) => {
      rules.forEach(([weight, pattern]) => {
        if (pattern.test(text)) scores[category] += weight;
      });
    });
    const bestScore = Math.max(...Object.values(scores));
    if (bestScore <= 0) return "company_market";
    return TIE_ORDER.find((category) => scores[category] === bestScore) || "company_market";
  }

  const api = { CATEGORY_DEFS, RULES, classify, textFor };
  root.AIIndustryTaxonomy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
