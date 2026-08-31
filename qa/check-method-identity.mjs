import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const spec = JSON.parse(
  readFileSync(join(root, "src/playbook-spec-v1.json"), "utf8"),
);
const identity = spec.method_identity;
const DEFAULT_MODULE_ID = "ia-panorama";
const MODULE_IDS = new Set([
  DEFAULT_MODULE_ID,
  "ocupado-productivo",
  "trabajo-amplificado",
  "trabajo-agentico",
]);
const EXPECTED_HTML_PAGES = 126;
const sha = (value) => createHash("sha256").update(value).digest("hex");
const fail = (code) => {
  throw new Error(code);
};
const files = (directory) =>
  readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
const rgb = (hex) =>
  hex
    .match(/[a-f\d]{2}/gi)
    .map((channel) => Number.parseInt(channel, 16) / 255);
const luminance = (hex) =>
  rgb(hex)
    .map((channel) =>
      channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
    )
    .reduce(
      (sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index],
      0,
    );
const contrast = (foreground, background) => {
  const values = [luminance(foreground), luminance(background)].sort(
    (a, b) => b - a,
  );
  return (values[0] + 0.05) / (values[1] + 0.05);
};
const validateSvg = (asset, payload) => {
  const text = payload.toString("utf8");
  const references = text.replace('xmlns="http://www.w3.org/2000/svg"', "");
  if (sha(payload) !== asset.sha256) fail("METHOD_MARK_HASH");
  if (!asset.rights) fail("METHOD_MARK_RIGHTS");
  if (!new RegExp(`<svg[^>]+viewBox=["']${asset.viewBox}["']`).test(text))
    fail("METHOD_MARK_VIEWBOX");
  if (/<(?:script|foreignObject|iframe|object|embed|image|text)\b/i.test(text))
    fail("METHOD_MARK_UNSAFE_TAG");
  if (/\bhref\s*=|https?:|\/\/|data:|javascript:|\\/i.test(references))
    fail("METHOD_MARK_EXTERNAL_REF");
  if (!/<path\b/.test(text)) fail("METHOD_MARK_OUTLINES");
  if (
    !text.includes("#ffd700") ||
    !text.includes("#0a122a") ||
    contrast("#ffd700", "#0a122a") < 4.5
  )
    fail("METHOD_MARK_CONTRAST");
};
const expectFailure = (code, run) => {
  try {
    run();
  } catch (error) {
    if (String(error).includes(code)) return;
  }
  fail(`MUTATION_FALSE_GREEN:${code}`);
};

if (identity.display_label !== "A²(R)E" || identity.role !== "method_mark")
  fail("METHOD_MARK_CONTRACT");
for (const asset of Object.values(identity.assets)) {
  const payload = readFileSync(join(root, "src", asset.path));
  validateSvg(asset, payload);
  const text = payload.toString("utf8");
  expectFailure("METHOD_MARK_UNSAFE_TAG", () =>
    validateSvg(
      { ...asset, sha256: sha(`${text}<script/>`) },
      Buffer.from(`${text}<script/>`),
    ),
  );
  expectFailure("METHOD_MARK_EXTERNAL_REF", () => {
    const mutated = text.replace(
      "<path ",
      '<path href="https://evil.example/x" ',
    );
    validateSvg({ ...asset, sha256: sha(mutated) }, Buffer.from(mutated));
  });
  expectFailure("METHOD_MARK_HASH", () =>
    validateSvg({ ...asset, sha256: "0".repeat(64) }, payload),
  );
  expectFailure("METHOD_MARK_RIGHTS", () =>
    validateSvg({ ...asset, rights: "" }, payload),
  );
  expectFailure("METHOD_MARK_VIEWBOX", () =>
    validateSvg({ ...asset, viewBox: "0 0 1 1" }, payload),
  );
  expectFailure("METHOD_MARK_CONTRAST", () => {
    const mutated = text.replaceAll("#ffd700", "#777777");
    validateSvg({ ...asset, sha256: sha(mutated) }, Buffer.from(mutated));
  });
}

const html = files(join(root, "dist")).filter((path) => path.endsWith(".html"));
if (html.length !== EXPECTED_HTML_PAGES)
  fail(`METHOD_MARK_ROUTE_COUNT:${html.length}`);
const expected = { landing: 2, playbook: 4, prompts: 1, workbook: 0, deck: 0, level0: 0, how: 0, resources_index: 0, intakes: 0 };
const obsolete = `A${String.fromCharCode(179)}`;
let relevant = 0;
let marks = 0;
let unstampedNestedResources = 0;
for (const path of html) {
  const content = readFileSync(path, "utf8");
  const page = content.match(/<body data-page="([^"]+)"/)?.[1];
  const moduleId = content.match(/<body[^>]+data-module-id="([^"]+)"/)?.[1];
  if (!(page in expected)) fail(`METHOD_MARK_PAGE:${relative(root, path)}`);
  if (!MODULE_IDS.has(moduleId))
    fail(`METHOD_MARK_MODULE:${relative(root, path)}:${moduleId}`);
  const count = content.match(/data-method-mark=/g)?.length ?? 0;
  // [EVIDENCE:M1_METHOD_IDENTITY] Only the original flat M1 surfaces carry A²(R)E.
  const wanted = moduleId === DEFAULT_MODULE_ID ? expected[page] : 0;
  if (count !== wanted)
    fail(`METHOD_MARK_COUNT:${relative(root, path)}:${count}`);
  if (content.includes(obsolete))
    fail(`METHOD_MARK_OBSOLETE:${relative(root, path)}`);
  marks += count;
  if (wanted > 0) {
    relevant += 1;
    if (!content.includes(identity.display_label))
      fail(`METHOD_MARK_ALT:${relative(root, path)}`);
  }
  if (moduleId !== DEFAULT_MODULE_ID) {
    if (!['deck', 'workbook', 'playbook', 'prompts'].includes(page))
      fail(`METHOD_MARK_NESTED_PAGE:${relative(root, path)}:${page}`);
    if (content.includes(identity.display_label))
      fail(`METHOD_MARK_NESTED_STAMP:${relative(root, path)}`);
    unstampedNestedResources += 1;
  }
}
if (relevant !== 18) fail(`METHOD_MARK_RELEVANT:${relevant}`);
if (marks !== 42) fail(`METHOD_MARK_TOTAL:${marks}`);
if (unstampedNestedResources !== 72)
  fail(`METHOD_MARK_NESTED_COUNT:${unstampedNestedResources}`);
expectFailure("METHOD_MARK_OBSOLETE", () => {
  if (`<main>${obsolete}</main>`.includes(obsolete))
    fail("METHOD_MARK_OBSOLETE");
});

const manifestPayload = readFileSync(join(root, "dist/build-manifest.json"));
const receiptPayload = readFileSync(join(root, "dist/build-receipt.json"));
const manifest = JSON.parse(manifestPayload.toString("utf8"));
const receipt = JSON.parse(receiptPayload.toString("utf8"));
if (
  manifest.method_identity.display_label !== identity.display_label ||
  manifest.method_identity.rendered_pages !== 18
)
  fail("METHOD_MARK_MANIFEST");
for (const [name, asset] of Object.entries(identity.assets)) {
  if (
    manifest.method_identity.assets[name] !== asset.sha256 ||
    manifest.outputs[asset.path] !== asset.sha256
  )
    fail(`METHOD_MARK_MANIFEST_ASSET:${name}`);
}
const canonical = (value) =>
  Array.isArray(value)
    ? `[${value.map(canonical).join(",")}]`
    : value && typeof value === "object"
      ? `{${Object.keys(value)
          .sort()
          .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`)
          .join(",")}}`
      : JSON.stringify(value);
const signed = (value) => ({ ...value, self_sha256: sha(canonical(value)) });
const outputBytes = Object.fromEntries(
  files(join(root, "dist"))
    .filter(
      (path) =>
        !path.endsWith("build-manifest.json") &&
        !path.endsWith("build-receipt.json"),
    )
    .map((path) => [relative(join(root, "dist"), path), readFileSync(path)]),
);
const parallelBrandAssets = new Set([
  "assets/metodologia-logo.svg",
  "assets/Poppins-Regular.ttf",
  "assets/Poppins-Bold.ttf",
  "assets/Montserrat-Variable.ttf",
  "assets/Poppins-Regular.woff2",
  "assets/Poppins-Bold.woff2",
  "assets/Montserrat-Variable.woff2",
  "assets/Poppins-OFL.txt",
  "assets/Montserrat-OFL.txt",
]);
const validateBuild = (manifestRaw, candidateReceipt, candidateOutputs) => {
  const candidateManifest = JSON.parse(manifestRaw.toString("utf8"));
  const { self_sha256: candidateSelf, ...candidateUnsigned } = candidateReceipt;
  if (candidateSelf !== sha(canonical(candidateUnsigned)))
    fail("METHOD_MARK_RECEIPT_SELF");
  if (candidateReceipt.manifest_sha256 !== sha(manifestRaw))
    fail("BUILD_MANIFEST_BINDING");
  if (
    candidateManifest.state !== "RENDERED_DRAFT" ||
    candidateReceipt.state !== "RENDERED_DRAFT"
  )
    fail("BUILD_STATE_CEILING");
  if (candidateManifest.publication_authorized !== false)
    fail("BUILD_PUBLICATION_AUTHORITY");
  if (
    candidateManifest.digital_brand?.network_required !== false ||
    candidateManifest.digital_brand?.publication_authority !== false
  )
    fail("BUILD_EFFECTS_AUTHORITY");
  const declared = Object.keys(candidateManifest.outputs).sort();
  const actual = Object.keys(candidateOutputs).sort();
  if (declared.some((path) => parallelBrandAssets.has(path)))
    fail("BUILD_PARALLEL_BRAND_ASSET");
  if (candidateReceipt.output_count !== declared.length)
    fail("BUILD_OUTPUT_COUNT");
  if (JSON.stringify(declared) !== JSON.stringify(actual))
    fail("BUILD_OUTPUT_TREE");
  for (const path of declared)
    if (sha(candidateOutputs[path]) !== candidateManifest.outputs[path])
      fail(`BUILD_OUTPUT_HASH:${path}`);
};
const rebound = (manifestRaw, changes = {}) => {
  const { self_sha256: _self, ...unsignedReceipt } = receipt;
  return signed({
    ...unsignedReceipt,
    ...changes,
    manifest_sha256: sha(manifestRaw),
  });
};
const mutatedManifest = (changes) => {
  const candidate = structuredClone(manifest);
  changes(candidate);
  const raw = Buffer.from(`${JSON.stringify(candidate, null, 2)}\n`);
  return [raw, rebound(raw)];
};
validateBuild(manifestPayload, receipt, outputBytes);
expectFailure("BUILD_OUTPUT_HASH:robots.txt", () =>
  validateBuild(manifestPayload, receipt, {
    ...outputBytes,
    "robots.txt": Buffer.from("mutated"),
  }),
);
expectFailure("BUILD_MANIFEST_BINDING", () => {
  const { self_sha256: _self, ...unsignedReceipt } = receipt;
  validateBuild(
    manifestPayload,
    signed({ ...unsignedReceipt, manifest_sha256: "0".repeat(64) }),
    outputBytes,
  );
});
expectFailure("BUILD_OUTPUT_COUNT", () => {
  const { self_sha256: _self, ...unsignedReceipt } = receipt;
  validateBuild(
    manifestPayload,
    signed({ ...unsignedReceipt, output_count: 0 }),
    outputBytes,
  );
});
expectFailure("BUILD_OUTPUT_TREE", () =>
  validateBuild(manifestPayload, receipt, {
    ...outputBytes,
    "unexpected.txt": Buffer.from("x"),
  }),
);
expectFailure("BUILD_OUTPUT_TREE", () => {
  const missing = { ...outputBytes };
  delete missing["robots.txt"];
  validateBuild(manifestPayload, receipt, missing);
});
expectFailure("BUILD_PARALLEL_BRAND_ASSET", () => {
  const bytes = Buffer.from("legacy font");
  const candidate = structuredClone(manifest);
  candidate.outputs["assets/Poppins-Regular.woff2"] = sha(bytes);
  const raw = Buffer.from(`${JSON.stringify(candidate, null, 2)}\n`);
  validateBuild(
    raw,
    rebound(raw, { output_count: Object.keys(candidate.outputs).length }),
    { ...outputBytes, "assets/Poppins-Regular.woff2": bytes },
  );
});
expectFailure("BUILD_STATE_CEILING", () => {
  const [raw, candidateReceipt] = mutatedManifest((candidate) => {
    candidate.state = "PUBLISHED";
  });
  validateBuild(raw, candidateReceipt, outputBytes);
});
expectFailure("BUILD_STATE_CEILING", () =>
  validateBuild(
    manifestPayload,
    rebound(manifestPayload, { state: "PUBLISHED" }),
    outputBytes,
  ),
);
expectFailure("BUILD_PUBLICATION_AUTHORITY", () => {
  const [raw, candidateReceipt] = mutatedManifest((candidate) => {
    candidate.publication_authorized = true;
  });
  validateBuild(raw, candidateReceipt, outputBytes);
});
expectFailure("BUILD_EFFECTS_AUTHORITY", () => {
  const [raw, candidateReceipt] = mutatedManifest((candidate) => {
    candidate.digital_brand.network_required = true;
  });
  validateBuild(raw, candidateReceipt, outputBytes);
});
expectFailure("BUILD_EFFECTS_AUTHORITY", () => {
  const [raw, candidateReceipt] = mutatedManifest((candidate) => {
    candidate.digital_brand.publication_authority = true;
  });
  validateBuild(raw, candidateReceipt, outputBytes);
});
if (receipt.method_identity.display_label !== identity.display_label)
  fail("METHOD_MARK_RECEIPT");

console.log(
  `[EVIDENCE:METHOD_IDENTITY] METHOD_IDENTITY_PASS pages=${html.length} relevant=${relevant} marks=${marks} nested_unstamped=${unstampedNestedResources} outputs=${Object.keys(manifest.outputs).length} mutations=24`,
);
