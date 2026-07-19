(function industryTaxonomyModule(root) {
  "use strict";

  const CATEGORY_DEFS = [
    { id: "ai_models", label: "AI模型", short: "AI模型", description: "模型、Agent、训练、推理、算法、Benchmark" },
    { id: "pc", label: "PC", short: "PC", description: "Notebook、Desktop、Workstation、客户端处理器、外设" },
    { id: "server", label: "Server", short: "Server", description: "Server系统、Server处理器、加速器、整机" },
    { id: "datacenter", label: "数据中心", short: "数据中心", description: "机架、网络、液冷、电力、云基础设施" },
    { id: "semiconductor", label: "半导体", short: "半导体", description: "晶圆代工、制造设备、先进封装、制程" },
    { id: "memory", label: "存储", short: "存储", description: "HBM、DRAM、NAND、GDDR、SSD" },
    { id: "display", label: "显示", short: "显示", description: "面板、显示器、OLED、LCD、MicroLED" },
    { id: "other", label: "其他", short: "其他", description: "暂时无法明确归入上述产业领域的内容" },
  ];

  const RULES = {
    ai_models: [
      [6, /\b(?:benchmark|eval|paper|arxiv|dataset|training|fine[- ]?tuning|reasoning|multimodal)\b|基准|论文|数据集|训练|推理|多模态/i],
      [5, /\b(?:llm|large language model|foundation model|ai agent|agentic|transformer|diffusion|rag)\b|大模型|基础模型|智能体/i],
      [4, /\b(?:gpt|claude|gemini|grok|llama|qwen|deepseek|mistral|kimi|glm|gemma)\b/i],
      [2, /\b(?:openai|anthropic|model|inference|attention|token)\b|模型|注意力/i],
    ],
    pc: [
      [7, /\b(?:pc|notebook|laptop|desktop|workstation|ai pc|copilot\+ pc|personal computer)\b|笔记本|台式机|工作站|个人电脑/i],
      [5, /\b(?:ryzen|core ultra|snapdragon x|macbook|chromebook|client gpu)\b/i],
      [4, /\b(?:cpu|npu|motherboard|webcam|headset|keyboard|touchpad|thunderbolt|usb-c)\b|处理器|主板|摄像头|耳机|键盘|触控板/i],
      [3, /\b(?:rtx\s?\d{3,4}|radeon|geforce|audio)\b|显卡|音频/i],
    ],
    server: [
      [8, /\b(?:ai server|server system|server platform|server cpu|server gpu)\b|AI Server|Server系统|服务器整机/i],
      [7, /\b(?:server|xeon|epyc|grace hopper|rack server)\b|服务器/i],
      [5, /\b(?:accelerator card|training accelerator|inference accelerator)\b|加速卡|训练加速器|推理加速器/i],
    ],
    datacenter: [
      [8, /\b(?:data center|datacenter|hyperscaler|cloud infrastructure|supercomputer)\b|数据中心|云基础设施|超级计算机/i],
      [6, /\b(?:nvlink|infiniband|cxl|ai networking|networking switch|optical interconnect|silicon photonics)\b|网络交换机|光互连|硅光/i],
      [5, /\b(?:rack|cluster|liquid cooling|power infrastructure|gpu cluster)\b|机架|集群|液冷|电力基础设施/i],
      [4, /\b(?:bandwidth|ethernet|kv[- ]?transfer)\b|带宽/i],
    ],
    semiconductor: [
      [8, /\b(?:foundry|wafer|advanced packaging|semiconductor fab|lithography)\b|晶圆|代工|先进封装|半导体制造|光刻/i],
      [7, /\b(?:tsmc|cxmt|asml|cowos|chiplet)\b|台积电|长鑫|阿斯麦|芯粒/i],
      [5, /\b(?:process node|fab equipment|semiconductor equipment|yield rate)\b|制程|晶圆厂设备|半导体设备|良率/i],
    ],
    memory: [
      [9, /\b(?:hbm\d?|dram|nand|gddr\d?|lpddr\d?|ddr\d?|memory chip)\b|内存|存储芯片/i],
      [7, /\b(?:ssd|solid state drive|micron|sk hynix|kioxia)\b|固态硬盘|美光|镁光|海力士/i],
      [5, /\b(?:memory price|memory shortage|memory capacity)\b|存储价格|存储短缺|存储产能/i],
    ],
    display: [
      [8, /\b(?:oled|lcd|microled|mini[- ]?led|display panel|monitor panel)\b|显示面板|显示器|面板/i],
      [6, /\b(?:boe|lg display|tcl csot|auo|innolux)\b|京东方|华星光电|友达|群创/i],
      [5, /\b(?:panel price|panel shipment|display technology)\b|面板价格|面板出货|显示技术/i],
      [3, /\bdisplay\b|显示/i],
    ],
  };

  const TIE_ORDER = ["memory", "display", "datacenter", "server", "pc", "ai_models", "semiconductor"];
  const MIN_SCORES = {
    ai_models: 4,
    pc: 3,
    server: 5,
    datacenter: 4,
    semiconductor: 5,
    memory: 5,
    display: 3,
  };

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

  function analyze(item) {
    const text = textFor(item);
    const titleText = [item?.title, item?.title_zh, item?.title_en, item?.title_original]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const scores = Object.fromEntries(CATEGORY_DEFS.map((category) => [category.id, 0]));

    Object.entries(RULES).forEach(([category, rules]) => {
      rules.forEach(([weight, pattern]) => {
        if (pattern.test(text)) scores[category] += weight;
        if (pattern.test(titleText)) scores[category] += Math.ceil(weight / 2);
      });
    });

    const explicit = Array.isArray(item?.industry_categories)
      ? item.industry_categories.filter((category) => CATEGORY_DEFS.some((definition) => definition.id === category))
      : [];
    const matched = TIE_ORDER.filter((category) => scores[category] >= MIN_SCORES[category]);
    const related = explicit.length ? explicit : (matched.length ? matched : ["other"]);
    const bestScore = Math.max(...related.map((category) => scores[category] || 0));
    const primary = related.find((category) => scores[category] === bestScore) || related[0];

    return {
      primary,
      related: Array.from(new Set([primary, ...related])),
      scores,
      confidence: primary === "other" ? "low" : (bestScore >= 8 ? "high" : "medium"),
    };
  }

  function classify(item) {
    return analyze(item).primary;
  }

  function classifyAll(item) {
    return analyze(item).related;
  }

  const api = { CATEGORY_DEFS, RULES, MIN_SCORES, analyze, classify, classifyAll, textFor };
  root.AIIndustryTaxonomy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
