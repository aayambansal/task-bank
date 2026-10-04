/**
 * Conservative display enrichment for the task directory.
 * Only supplied metadata and instruction text are used; source excerpts are kept
 * as whole paragraphs/list items (never cut at a character offset).
 */
export const DOMAIN_OPTIONS = Object.freeze([
  'AI research', 'Language models', 'Computer vision', 'Reinforcement learning',
  'ML systems', 'Data curation', 'Scientific computing', 'Software engineering',
  'Mathematics', 'Reproduction', 'AI safety', 'Agents',
]);

const UNKNOWN = 'Not specified in the published source.';
const BROAD = new Set(['Research suites', 'Model development', 'ML experimentation', 'Reproduction', 'ML systems']);
const AI_SUITES = new Set([
  're-bench', 'posttrainbench', 'innovatorbench', 'researchgym', 'mlrc-bench',
  'fml-bench', 'mle-bench', 'mlagentbench', 'mlgym', 'mle-dojo', 'mlr-bench',
  'mls-bench', 'airs-bench', 'weirdml', 'paperbench', 'exp-bench', 'scientist-bench',
  'mlreplicate', 'llm-speedrunning', 'scale-rsi-bench', 'ai4ai-bench',
  'rsibench-data', 'curatebench', 'curation-bench', 'curation-bench-pro',
  'ft-dojo', 'ft-bench', 'agent2-rl-bench',
]);
const LM_SUITES = new Set(['posttrainbench', 'rsibench-data', 'curatebench', 'ft-dojo', 'ft-bench', 'agent2-rl-bench', 'llm-speedrunning']);
const unique = (xs) => [...new Set(xs.filter(Boolean))];
const compact = (s) => String(s ?? '').replace(/\s+/g, ' ').trim();
const plain = (s) => compact(String(s ?? '').replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/[`*_]/g, ''));
const unknown = (s) => !compact(s) || /^not (?:specified|available|published|released)(?:[. ]|$)/i.test(compact(s));
const clean = (s) => String(s ?? '').replace(/\\u2019/g, '’').replace(/\\u2013/g, '–').replace(/\\u2014/g, '—').trim();
const fragment = (s) => /(?:…|\.\.\.)\s*$/.test(s) || /\b(?:and|or|the|a|an|of|to|with|for|from|is|are|impo)\s*$/i.test(plain(s));
const boilerplate = (s) => /^(?:Source:|Attribution:|This (?:reader|reading guide|is a (?:condensed|paraphrased|structured))|Based on:|Inspired by |Remember:|You are (?:an? )?(?:expert|autonomous|AI|research agent)|This is a Machine Learning project)/i.test(plain(s)) || /^\[(?:Read|Open|Full|Complete) [^]*\]\(https?:/i.test(s);

/** Parse Markdown paragraphs, complete list items, and fenced code blocks. */
function blocksFromMarkdown(markdown) {
  const lines = clean(markdown).replace(/<!--[^]*?-->/g, '').replace(/^You are a expert[^]*?following instruction\.\s*/i, '').replace(/^You are an expert in Trion[^]*?provided function information\.\s*/i, '').replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let heading = '', buffer = [], fence = null, code = [];
  const flush = () => {
    const text = buffer.join('\n').trim();
    if (text) blocks.push({ heading, text, code: false });
    buffer = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fenceMatch = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      code.push(line);
      if (fenceMatch && fenceMatch[1][0] === fence[0] && fenceMatch[1].length >= fence.length) {
        blocks.push({ heading, text: code.join('\n'), code: true });
        fence = null; code = [];
      }
      continue;
    }
    if (fenceMatch) { flush(); fence = fenceMatch[1]; code = [line]; continue; }
    const atx = line.match(/^\s{0,3}#{1,6}\s+(.+?)\s*#*$/);
    const nextSetext = lines[i + 1]?.match(/^\s*(?:={3,}|-{3,})\s*$/);
    const label = line.match(/^\s*(?:\*\*)?((?:Task Description|Functional Description|Wrapper Entry Information|Math|other|Input|Output|Constraints|Evaluation|Scoring|Submission|Data|INSTRUCTIONS))(?:\*\*)?:\s*(.*)$/i);
    if (atx || (line.trim() && nextSetext) || label) {
      flush(); heading = plain(atx?.[1] ?? label?.[1] ?? line);
      if (nextSetext && !atx && !label) i++;
      if (label?.[2]) buffer.push(label[2]);
      continue;
    }
    if (/^\s*---+\s*$/.test(line)) { flush(); heading = 'Source attribution'; continue; }
    if (!line.trim()) { flush(); continue; }
    // A bullet may span many wrapped source lines. Keep those lines together.
    if (/^\s{0,3}(?:[-+*]|\d+[.)])\s+/.test(line)) flush();
    buffer.push(line);
  }
  flush();
  if (code.length) blocks.push({ heading, text: code.join('\n'), code: true });
  return blocks;
}

function displayBlock(b) {
  if (b.code) return b.text;
  return b.text.replace(/^\s*>\s?/gm, '').replace(/^\s*(?:[-+*]|\d+[.)])\s+/, '').replace(/\n[ \t]*/g, ' ').trim();
}
function usable(b) {
  return !b.code && !/source (?:attribution|coverage)|prohibited source resources|literature context|related smoke|variants/i.test(b.heading)
    && !boilerplate(displayBlock(b)) && !fragment(displayBlock(b))
    && !/^\s*\|/.test(b.text) && plain(b.text).length > 25;
}
function select(blocks, headingPattern, max = 4, { code = false } = {}) {
  return unique(blocks.filter((b) => headingPattern.test(b.heading)
    && (code ? !boilerplate(displayBlock(b)) : usable(b)))
    .map(displayBlock)).slice(0, max);
}
function sentences(s, max = 3) {
  const text = clean(s);
  if (text.length < 1600 || /```|\n[-*]|\$\$/.test(text)) return text;
  // Intl segments complete sentences; it does not truncate file paths or decimals.
  const segments = [...new Intl.Segmenter('en', { granularity: 'sentence' }).segment(text)].map((x) => x.segment);
  return segments.slice(0, max).join('').trim();
}
function safeMetadata(s) {
  const text = clean(s);
  return text && !unknown(text) && !fragment(text) ? text : '';
}
function metadataList(value) {
  const values = Array.isArray(value) ? value : value ? [value] : [];
  // Old ingestion sometimes retained single wrapped lines, not sentences. Do not
  // promote those fragments into a factual brief; source blocks take precedence.
  return values.map(safeMetadata).filter((s) => s && /[.!?]$|[`\])}]$/.test(s) && !boilerplate(s));
}

export function classifyDomains(task, benchmark = {}, briefTask = '') {
  const id = task.benchmarkId || benchmark.id;
  // Only the task's topic is classified: agent harness boilerplate and an entire
  // paper's reference list would create spurious language-model / agent labels.
  const topic = plain([task.name, BROAD.has(task.category) ? '' : task.category, ...(task.tags || []), briefTask || task.objective].join(' ')).toLowerCase().replace(/[‐‑–—-]/g, ' ');
  const title = plain([task.name, BROAD.has(task.category) ? '' : task.category, ...(task.tags || [])].join(' ')).toLowerCase().replace(/[‐‑–—-]/g, ' ');
  const set = new Set();
  if (AI_SUITES.has(id) || /\b(?:machine learning|deep learning|neural network|model training|finetun|fine-tun|post-train|pre-train|llm|language model)\b/.test(topic)) set.add('AI research');
  if (LM_SUITES.has(id) || (task.tags || []).some(t => /^(?:text|nlp|natural language processing)$/i.test(t)) || /\b(?:llms?|language models?|language modeling|language modelling|nlp|natural language|qwen\w*|llama\w*|gemma\w*|gpt-?\d*|smollm\w*|mistral|text generation|text classification|sentiment|summarization|translation|question answering|table qa|bert|roberta|mnli|glue|prompt tuning|instruction tuning|tokenization)\b/.test(topic)) set.add('Language models');
  if (/\b(?:computer vision|image(?:net)?|images|visual|vision|video|object detection|segmentation|cifar\d*|fashion.?mnist|mnist|fmnist|point clouds?|diffusion model|stable diffusion|llava|coco|ocr|clip|blip|deepfake|retinopathy|ct scan|mammograph)\b/.test(topic)) set.add('Computer vision');
  if (/\b(?:reinforcement learning|reinforcement-learning|rl|rlhf|grpo|ppo|q.learning|sac|mujoco|gymnasium|dqn|policy gradient|policy optimization|replay buffers?|atari|breakout|mountaincar|metamaze|control policy|robotic|robotics)\b/.test(topic)) set.add('Reinforcement learning');
  if (['kernelbench', 'tritonbench', 'llm-speedrunning'].includes(id) || /\b(?:mlsys|ml systems|gpu kernel|cuda|triton|inference optimization|inference acceleration|sparse attention|prefill|language model inference|quantization|dequantization|kv.cache|gemm|training throughput|distributed training|model compression|training speed|optimizer efficiency)\b/.test(topic)) set.add('ML systems');
  if (['rsibench-data','curatebench','curation-bench','curation-bench-pro'].includes(id) || /\b(?:data curation|data-centric|data selection|dataset selection|data construction|dataset construction|data synthesis|synthetic data|training data strategy|pool pruning|curat(?:e|ion|ing)|data mixture|deduplication|dataset discovery)\b/.test(topic)) set.add('Data curation');
  if (id === 'scienceagentbench' || /\b(?:scientific computing|computational (?:chemistry|biology|physics)|chemistry|molecular|molecule|molecules|protein|genomic|genome|materials|physics|astronomy|astrometry|fluid dynamics|partial differential|pde|quantum|climate|weather|aerodynamic|neuroscience|numerical integration|numerical simulation|finite.element)\b/.test(topic)) set.add('Scientific computing');
  if (id === 'frontierswe-v2' || /\b(?:software engineering|code generation|code repair|program synthesis|codecontests|compiler|cryptograph|encryption|decryption|code optimization|unit test|debugging|software toolkit)\b/.test(topic)) set.add('Software engineering');
  if (/\b(?:mathematics|mathematical|aime|gsm8k|theorem|3.?sat|sat solver|combinatorial optimization|convex optimization|linear programming|geometric programming|integer programming|graph algorithm|shortest path|floyd.?warshall|number theory|symbolic regression)\b/.test(topic)) set.add('Mathematics');
  if (['paperbench','mlreplicate'].includes(id) || /\bpaper reproduction\b/.test(topic)) set.add('Reproduction');
  if (/\b(?:ai safety|ai alignment|jailbreak|backdoor|adversarial robustness|machine unlearning|model unlearning|safety alignment|defensive|interpretability|mechanistic interpretability|red.team|alignment)\b/.test(topic)) set.add('AI safety');
  if (/\b(?:agentic|multi.agent|llm agent|tool.use|tool use|function calling|tool calling|agent (?:swarm|scaffold|harness|memory|system|architecture)|web navigation|webshop|alfworld|browser agent|embodied agent)\b/.test(topic) || /^(?:agents|ai models & agents)$/i.test(task.category || '')) set.add('Agents');
  // Algorithm engineering is broader than ML. Classify its concrete content;
  // avoid marking all 154 optimization programs as AI research.
  if (id === 'algotune' && set.size === 0) set.add('Scientific computing');
  if (id !== 'algotune' && ['Language models', 'Computer vision', 'Reinforcement learning', 'Data curation', 'AI safety', 'Agents'].some((d) => set.has(d))) set.add('AI research');
  return DOMAIN_OPTIONS.filter((d) => set.has(d));
}

function fieldFor(task, domains, override) {
  if (override.field) return clean(override.field);
  if (task.category && !BROAD.has(task.category)) return task.category;
  const suites = {
    'kernelbench': 'GPU kernel optimization', 'tritonbench': 'GPU kernel optimization',
    'algotune': 'Algorithm optimization', 'llm-speedrunning': 'Language model training speed',
    'posttrainbench': 'Language model post-training', 'mle-bench': 'Predictive modeling',
    'mle-dojo': 'Predictive modeling', 'mlr-bench': 'Open-ended ML research',
    'paperbench': 'Paper reproduction', 'mlreplicate': 'Paper reproduction',
  };
  const specificTags = (task.tags || []).filter((t) => !/^(?:official|published|current|retired|canonical|task family|protected scoring|held-out|research brief|kaggle|preparation manifest|test environment|source|public|iclr\d|neurips\d|icml\d|level\d|gpu|cpu|benchmark|autoresearch|machine-learning|hints|paper reproduction|experiment type|record \d|post-training|qwen|gemma|smollm|nanogpt|task[12]|8[×x])/i.test(t));
  if (task.benchmarkId === 'mle-dojo' && specificTags.length) return specificTags.slice(0, 2).join(' · ');
  if (task.benchmarkId === 'fml-bench' && specificTags.length) return specificTags[0];
  if (task.benchmarkId === 'scienceagentbench' && specificTags.length) return specificTags[0];
  if (suites[task.benchmarkId]) return suites[task.benchmarkId];
  const topicDomains = domains.filter((d) => d !== 'AI research');
  return topicDomains[0] || (domains.includes('AI research') ? 'ML research' : 'Research and engineering');
}

/** Keep the complete allocation/budget semantics, especially ranges and scope. */
export function resourceLabel(value) {
  if (!compact(value)) return 'Not specified';
  return compact(value).replace(/\bNVIDIA\s+/g, '').replace(/\(suite-level information\)/g, '(suite-level)').replace(/Not specified in the published source\.?$/i, 'Not specified');
}
export function timeLabel(value) {
  if (!compact(value)) return 'Not specified';
  return compact(value).replace(/\(suite-level information\)/g, '(suite-level)').replace(/Not specified in the published source\.?$/i, 'Not specified');
}

export function enrichTask(task, benchmark = {}, instructions = '', override = {}) {
  const blocks = blocksFromMarkdown(instructions);
  const prose = blocks.filter(usable).filter(b => !(/(?:Optimization )?Task:?$/i.test(plain(b.text)) && plain(b.text).length < 90));
  const objectiveHeading = /^(?:(?:research|task|core) )?(?:objective|goal|assignment|question|task|task context|published task summary|published experimental setting|task description|functional description)$/i;
  let taskText = select(blocks, objectiveHeading, 1)[0];
  if (!taskText) taskText = prose.find((b) => !/resource|deliverable|submission|evaluation|grader|scor|license|reference|paper$|literature/i.test(b.heading)) && displayBlock(prose.find((b) => !/resource|deliverable|submission|evaluation|grader|scor|license|reference|paper$|literature/i.test(b.heading)));
  taskText ||= safeMetadata(task.objective) || safeMetadata(task.summary) || UNKNOWN;
  // Paper titles identify the actual reproduction target; the common prompt alone
  // would otherwise produce twenty indistinguishable briefs.
  if (['paperbench','mlreplicate'].includes(task.benchmarkId) && /^(?:You are tasked|You have been provided|Your task is to replicate)/.test(taskText)) taskText = `Reproduce the core contributions of “${task.name}”.`;
  if (task.benchmarkId === 'mlr-bench') taskText = `Develop and evaluate a research contribution within the brief “${task.name}”.\n\n${sentences(taskText, 2)}`;
  if (task.benchmarkId === 'kernelbench') {
    const reference = blocks.find((b) => b.code && /class Model/.test(b.text));
    const doc = reference?.text.match(/class Model[^]*?"""([^]*?)"""/)?.[1]?.split(/\n\s*(?:Parameters|Args|Returns):/)[0].trim();
    taskText = `Optimize the ${task.name} workload while preserving the reference PyTorch behavior.${doc ? '\n\n' + compact(doc) : ''}`;
  }
  if (task.benchmarkId === 'tritonbench') taskText = taskText.replace(/^You are a expert[\s\S]*?following instruction\.\s*/i, '');
  if (task.benchmarkId === 'frontierswe-v2') {
    const quoted = blocks.find((b) => /^>/.test(b.text));
    if (quoted) taskText = displayBlock(quoted);
  }
  // AIRS puts its concrete assignment after a generic project preamble.
  if (task.benchmarkId === 'airs-bench') {
    const concrete = prose.find((b) => /(?:^|\n)\s*TASK:\s*/i.test(b.text));
    if (concrete) taskText = displayBlock(concrete).replace(/^TASK:\s*/i, '');
  }
  taskText = override.task ? clean(override.task) : sentences(taskText, 3);

  let world = select(blocks, /(?:^|\b)(?:starting point|setup|environment|world|wrapper entry information|math|other|what you are given|the loop|budgets and hard limits|development data|data and work|data metadata|input files|data preparation|experimental contract|reference methods and resources|editable files|execution contract|work surface|work to perform|constraints|competition rules|rules|information on the setup|available starting point|input|data)(?:\b|$)/i, 8)
    .filter((s) => s !== taskText && !/^Resources:/.test(s));
  // Source sections are preferred over old arrays of chopped lines. Add only
  // complete constraints that contribute something absent from the excerpts.
  if (!world.length) {
    world = prose.filter((b) => /(?:provided|supplied|available|editable|read.only|must not|may not|cannot|do not|fixed|baseline|dataset|train split|example heuristic|training split|test split|workspace)/i.test(b.text)
      && !displayBlock(b).startsWith(taskText) && !taskText.startsWith(displayBlock(b)) && !/(?:Source attribution|Literature|scoring|evaluation)/i.test(b.heading)).slice(0, 3).map(displayBlock);
  }
  if (!world.length) world = metadataList(task.constraints).slice(0, 4);
  const inputCode = blocks.filter(b => b.code && /^(?:input files|data|dataset structure)$/i.test(b.heading)).slice(0, 1).map(displayBlock);
  if (inputCode.length) world = [...inputCode, ...world].slice(0, 8);
  if (task.benchmarkId === 'kernelbench') {
    // Keep the executable workload in the original-instructions view. The brief
    // describes its interface and uses only complete, short generator functions.
    const reference = blocks.find((b) => b.code && /class Model/.test(b.text));
    if (reference) {
      const signatures = [...reference.text.matchAll(/^\s*def (__init__|forward)\(([^\n]*)\)(?:\s*->[^:]+)?:/gm)].map(m => `\`${m[1]}(${m[2]})\``);
      world = ['Use the supplied PyTorch workload and its input generators as the reference for behavior and numerical correctness.'];
      if (signatures.length) world.push('Reference interfaces: ' + signatures.join('; ') + '.');
      const generator = reference.text.match(/^def get_init_inputs\([^]*?(?=^\S|^```|$(?![^]))/m)?.[0]?.trim();
      if (generator && generator.length <= 1200) world.push('Constructor inputs:\n\n```python\n' + generator + '\n```');
      world.push('The supplied `get_inputs()` defines the test tensors, shapes and dtypes; keep this input contract. The complete generator and workload are in the original instructions.');
    }
  }
  if (task.benchmarkId === 'tritonbench' && !world.length) world = prose.slice(1, 4).map(displayBlock);
  if (override.world) world = override.world.map(clean);
  if (!world.length) world = [UNKNOWN];
  if (!override.world) {
    world.push('Compute: ' + resourceLabel(task.gpu || benchmark.gpu));
    world.push('Time: ' + timeLabel(task.timeBudget || benchmark.timeBudget));
  }

  let submission = select(blocks, /^(?:deliverable|deliverables|required result|output|submission|submission file|what to submit|final submission|the entry point|entry point|submission format|your submission|wrapper entry information|deliverable and evaluation)$/i, 8, { code: true }).join('\n\n');
  const genericSubmission = /^(?:Source brief specifies|Task-specific|See |Not specified)/i.test(task.submission || '');
  if (!submission && !genericSubmission) submission = safeMetadata(task.submission);
  if (!submission) {
    submission = prose.filter((b) => /(?:submi(?:t|ssion)|deliverable|save (?:the|your|a)|write (?:the|your|`|\/)|final (?:artifact|model|checkpoint)|output file)/i.test(b.text)
      && !/evaluation|scor|source attribution|literature/i.test(b.heading)).slice(0, 2).map(displayBlock).join('\n\n');
  }
  if (!submission && !genericSubmission) submission = safeMetadata(task.submission);
  if (task.benchmarkId === 'algotune' && submission) submission = `${safeMetadata(task.submission) || 'Implement the task solve interface.'}\n\nRequired output:\n${submission}`;
  submission = override.submission ? clean(override.submission) : submission || UNKNOWN;

  let grader = select(blocks, /^(?:(?:final|formal|hidden|test|task|comparative|published) )?(?:evaluation|scoring|grader|grading|evaluation metrics|metric|metrics|measurement|evaluation boundary|submission and scoring|evaluation and budget)$/i, 6);
  if (!grader.length) grader = [safeMetadata(task.evaluation)].filter(Boolean);
  if (!grader.length) grader = prose.filter((b) => /(?:score is|scored on|evaluated (?:on|using)|metric is|measured (?:on|using|by)|hidden test|held.out test)/i.test(b.text)).slice(0, 3).map(displayBlock);
  if (override.grader) grader = override.grader.map(clean);
  if (!grader.length) grader = [UNKNOWN];

  const domains = classifyDomains({ ...task, name: override.name || task.name, category: override.field || task.category }, benchmark, taskText);
  const result = {
    domains,
    field: fieldFor(task, domains, override),
    brief: { task: taskText, world: unique(world), submission, grader: unique(grader) },
    resourceLabel: resourceLabel(task.gpu || benchmark.gpu),
    timeLabel: timeLabel(task.timeBudget || benchmark.timeBudget),
  };
  for (const key of ['name', 'sourceUrl', 'sources']) if (override[key]) result[key] = override[key];
  return result;
}
