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
  ];

  const EVENT_DEFS = [
    { id: "product_release", label: "产品发布" },
    { id: "technology", label: "技术进展" },
    { id: "review", label: "性能评测" },
    { id: "pricing", label: "价格变化" },
    { id: "supply_demand", label: "供需变化" },
    { id: "capacity", label: "产能扩张" },
    { id: "financial", label: "财报投资" },
    { id: "ma_cooperation", label: "并购合作" },
    { id: "strategy", label: "企业战略" },
    { id: "policy", label: "政策监管" },
    { id: "people", label: "人事组织" },
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

  const EVENT_RULES = {
    product_release: /\b(?:launch|release|announce|unveil|debut|available|rollout)\b|发布|推出|上市|亮相|开售/i,
    technology: /\b(?:architecture|technology|breakthrough|prototype|design|port(?:s|ed)?|reduce[sd]?|improve[sd]?)\b|架构|技术|突破|原型|设计|移植|降低|提升/i,
    review: /\b(?:review|benchmark|test(?:ed|ing)?|performance|fps|latency|throughput)\b|评测|基准|性能|延迟|吞吐/i,
    pricing: /\b(?:price|pricing|discount|cost|expensive|cheap|promo)\b|价格|降价|涨价|折扣|成本|促销/i,
    supply_demand: /\b(?:supply|demand|shortage|inventory|shipment|backlog|tam)\b|供应|需求|短缺|库存|出货|积压|市场规模/i,
    capacity: /\b(?:capacity|fab expansion|expand production|new fab)\b|产能|扩产|新建晶圆厂/i,
    financial: /\b(?:earnings|revenue|profit|capex|funding|raised|investor|valuation|investment|cost surprise|multibillion[- ]dollar cost)\b|财报|营收|利润|资本开支|融资|投资者|估值|投资/i,
    ma_cooperation: /\b(?:acquisition|acquire|merger|partnership|collaboration|joint venture)\b|收购|并购|合作|合资/i,
    strategy: /\b(?:strategy|roadmap|agenda|commercialization|market entry|exit market)\b|战略|路线图|议程|商业化|进入市场|退出市场/i,
    policy: /\b(?:regulation|policy|antitrust|tariff|sanction|white house|government|trump|president|federal)\b|监管|政策|反垄断|关税|制裁|白宫|政府/i,
    people: /\b(?:resign|depart|left|joins|appointed|layoff|restructur)\b|离职|加入|任命|裁员|重组/i,
  };

  const TIE_ORDER = ["memory", "display", "datacenter", "server", "pc", "ai_models", "semiconductor"];
  const NON_INDUSTRY_PATTERNS = [
    /\b(?:charity auction|celebrity|fashion|trademark leather jacket|red carpet)\b|慈善拍卖|明星|时尚|红毯/i,
  ];
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

  function eventTagsForText(text, domains = []) {
    const technicalOnly = new Set(["product_release", "technology", "review"]);
    return EVENT_DEFS
      .filter((event) => (!technicalOnly.has(event.id) || domains.length > 0) && EVENT_RULES[event.id].test(text))
      .map((event) => event.id);
  }

  function analyze(item) {
    const text = textFor(item);
    const titleText = [item?.title, item?.title_zh, item?.title_en, item?.title_original].filter(Boolean).join(" ").toLowerCase();
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
    const related = explicit.length
      ? explicit
      : TIE_ORDER.filter((category) => scores[category] >= MIN_SCORES[category]);
    const bestScore = related.length ? Math.max(...related.map((category) => scores[category])) : 0;
    const primary = related.find((category) => scores[category] === bestScore) || related[0] || "unclassified";

    return {
      primary,
      related: Array.from(new Set(related)),
      eventTags: NON_INDUSTRY_PATTERNS.some((pattern) => pattern.test(text)) ? [] : eventTagsForText(text, related),
      scores,
      confidence: !related.length ? "low" : (bestScore >= 8 ? "high" : "medium"),
    };
  }

  function classify(item) {
    return analyze(item).primary;
  }

  function classifyAll(item) {
    return analyze(item).related;
  }

  function classifyEvents(item) {
    return analyze(item).eventTags;
  }

  function eventLabels(item, limit = 2) {
    const ids = classifyEvents(item);
    return EVENT_DEFS
      .filter((event) => ids.includes(event.id))
      .slice(0, limit)
      .map((event) => event.label);
  }

  const api = {
    CATEGORY_DEFS,
    EVENT_DEFS,
    RULES,
    EVENT_RULES,
    MIN_SCORES,
    analyze,
    classify,
    classifyAll,
    classifyEvents,
    eventLabels,
    textFor,
  };
  root.AIIndustryTaxonomy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
