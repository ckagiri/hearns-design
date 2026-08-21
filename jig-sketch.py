"""
Jig runner — happy-path sketch, v4.

Pseudocode, not runnable. Elisions marked `...`.
Section refs are to harness-core-v3 (§C) and harness-policy-v3 (§P).
Rewrite of v2; v4 adds the registries (tools, skills, checks, hooks), the
emit-time edge gate, and the dep predicate. Diffs at the foot.

Shape of the thing:

    worker loop ──claim──► run_jig ──► JigResult ──► plan_emissions ──► commit
                              │
                              ├── render()        layers 0–8, harness-owned
                              ├── port.complete() cache below the port, over wire bytes
                              ├── dispatch_tool() five checks, then normalize
                              ├── parse + repair  bounded, explicit, one turn
                              └── run_oracle()    hidden, fresh container, four states

One runner for every role. Roles differ only in data.
"""

# ══════════════════════════════════════════════════════════════════════
# 0a. Canonicalization.  Load-bearing for config_hash, kind_hash and the
#     cache key, and the classic subtle-bug generator: key order, unicode
#     normalization form, float repr, escaping, whether 1 and 1.0 agree.
#     Each of those yields a hash stable on YOUR machine and unstable across
#     a Python or locale change — presenting as a cache miss you blame on
#     the model.  json.dumps(sort_keys=True) fixes NEITHER float repr nor
#     unicode form.  Use an RFC 8785 (JCS) implementation, and pin it: a
#     canonicalizer upgrade moves every key you hold.  (R-new-6)
# ══════════════════════════════════════════════════════════════════════

from jcs import canonicalize as canonical_bytes    # RFC 8785. pinned.


# ══════════════════════════════════════════════════════════════════════
# 0. Vocabularies.  Closed enums, because every one of these lands in a
#    ledger column that gets grouped by later.  A model-authored string
#    here fragments every query over outcomes forever.
# ══════════════════════════════════════════════════════════════════════

class Outcome(StrEnum):
    OK               = "ok"           # terminal, work landed
    EXPANDED         = "expanded"     # terminal, children emitted
    BLOCKED          = "blocked"      # needs something outside ownership
    MISCLASSIFIED    = "misclassified"  # the CARD was the wrong shape
    EXPLORATION_CAP  = "exploration_cap"  # we ran out of turns. NOT the same thing.
    SCHEMA_VIOLATION = "schema_violation"
    REFUSED          = "refused"


# §C10's allow-list. Infra failures resume WITHOUT consuming an attempt;
# everything else does. The adapter's only job at the bottom of the port
# is to map its provider's exceptions into this. (Borrowed shape: one
# taxonomy, many adapters.)
class FailureClass(StrEnum):
    RATE_LIMITED       = "rate_limited"        # ─┐
    OVERLOADED         = "overloaded"          #  │ free retry
    TIMEOUT            = "timeout"             # ─┘
    CONTEXT_EXCEEDED   = "context_exceeded"    # ─┐
    PROVIDER_REFUSED   = "provider_refused"    #  │ consumes an attempt
    MALFORMED_OUTPUT   = "malformed_output"    #  │
    TURN_LIMIT         = "turn_limit"          # ─┘ NEVER a success (RED-000)
    HARNESS_BUG        = "harness_bug"         # quarantine, do not retry

FREE_RETRY = {FailureClass.RATE_LIMITED, FailureClass.OVERLOADED, FailureClass.TIMEOUT}


# ADR-0006. A dependency is satisfied by `done` and by nothing else.
#
# `blocked` is terminal for the WORKER — lease released, row no longer leased —
# but its result_summary describes an intention, not an outcome. A child handed
# that summary reads `Exposes: X` for an X that does not exist, and the best
# available attempt is to block too, after a workspace build, a container, a
# template clone and a model call.
#
# The alternative — let it through and have dep_summaries render a warning —
# is rule 25's anti-pattern: an instruction the card is asked to honour rather
# than a state it was never given. The predicate is the same gate for free and
# cannot be talked out of.
#
# Accepted cost: a parent that built its interface and THEN blocked on
# something unrelated stalls its children anyway. Deliberate. The alternative
# asks the board how much of a parent's work landed, which it cannot know.
# A partial block deserves a human verb.
SATISFIES_DEP = {"done"}


# ══════════════════════════════════════════════════════════════════════
# 1. Registries.  Everything a jig NAMES lives here, by string.
#    Nothing in a jig executes.  This is what makes config_hash mean
#    something (§C8) — the jig set is data and hashes cleanly.
# ══════════════════════════════════════════════════════════════════════

TOOLS:  dict[str, ToolImpl]  = {}   # name -> schema, fn, normalizer, side_effect_class
CHECKS: dict[str, CheckImpl] = {}   # 'command' | 'lsp_diagnostics' | ...
SHAPES: dict[str, ShapeFn]   = {}   # 'children' | 'gate' | 'artifact' | 'selection'
SKILLS: dict[str, list[str]] = {}   # KIND -> skill names.  Loaded from
                                    # harness/config/skills.yaml. Six lines,
                                    # written by hand at pin time. See §Skills.

# HOOKS is the one registry worth a library.  A plain dict[str, list[Fn]] has a
# specific failure: a typo'd hook name registers a function that silently never
# fires, and you find out when workspace reset stops happening and cards start
# inheriting each other's state — presenting as flaky cards, not as a missing
# hook.  pluggy validates implementations against declared specs AT REGISTRATION,
# so a misspelled name or wrong signature raises at import.  Ordering without a
# convention; firstresult where one answer wins.  Outside the pin, because hooks
# do not render into prompts.
#
# NO ENTRY-POINT DISCOVERY.  A hook that arrives by being pip-installed is a
# hook that is not in your config.  Register explicitly.
hooks = pluggy.PluginManager("h3")
hooks.add_hookspecs(hookspecs)      # post_claim, pre_commit, post_commit
# hooks.load_setuptools_entrypoints("h3")   ← deliberately not called


@dataclass(frozen=True)
class ToolImpl:
    fn: Callable
    normalize: Callable[[str], str]  # REQUIRED. see dispatch_tool, and R-new-5 at foot
    side_effect: str                 # read|workspace_write|scoped_exec|escaping|irreversible

    @cached_property
    def schema(self) -> dict:
        """DERIVED from fn, never hand-written.

        A hand-written schema drifts from the signature silently, and the drift
        surfaces as `invalid_args` denials that look like model misbehaviour.
        Deriving it makes check 2 in dispatch_tool structurally unable to
        disagree with check 1 — the same argument as normalize being
        non-optional at the type level."""
        return TypeAdapter(self.fn).json_schema()


# ── §Tools ────────────────────────────────────────────────────────────
# Why this registry is not MCP, or any external tool provider:
#
#   1. Tool schemas are LAYER 3, therefore inside config_hash. A server
#      upgrade changes what every card saw with nothing in the design
#      moving. R60 by another door.
#   2. A server lifecycle inside the container adds failure modes to the
#      exact layer Gate A is trying to prove — something must start it,
#      health-check it, and kill it before `docker kill` does.
#   3. `normalize` has no external equivalent. No provider offers a
#      stable-bytes guarantee, so you would wrap every tool anyway and keep
#      the dependency for nothing.
#
# The real set is six: read, write, edit, bash, grep, ls. A few hundred lines
# with normalizers, all of it wanting OUR side_effect classification and OUR
# quota keying. Read smolagents' defaults for shape; import nothing.

TOOLS["read"]  = ToolImpl(fn=read_file,  normalize=strip_abs_paths,   side_effect="read")
TOOLS["ls"]    = ToolImpl(fn=list_dir,   normalize=sort_lines,        side_effect="read")
TOOLS["grep"]  = ToolImpl(fn=grep,       normalize=sort_lines,        side_effect="read")
TOOLS["write"] = ToolImpl(fn=write_file, normalize=noop,              side_effect="workspace_write")
TOOLS["edit"]  = ToolImpl(fn=edit_file,  normalize=noop,              side_effect="workspace_write")
TOOLS["bash"]  = ToolImpl(fn=run_bash,   normalize=strip_timings_and_paths,
                                                                      side_effect="scoped_exec")


@dataclass(frozen=True)
class Jig:
    """A manifest. Loaded from YAML, resolved against config_version."""
    system_ref: str                  # layer 0 — a PATH, not inline text. Two kinds that
                                     # differ only in their skill set share one jig body;
                                     # inlining it would make §P2's "jig count is bounded
                                     # by kind" expensive to honour.
    preamble: str                    # layer 1
    tools: list[str]                 # layer 3 — per ROLE; absence is the gate (rule 135)

    # NOTE: `skills` is NOT here. v3 had it, and that was wrong: Role.kinds is a
    # list and Role.jig is one jig, so a role serving two kinds gave both the
    # same skills — contradicting skills being per-kind. The lookup is keyed off
    # the CARD instead: SKILLS[task.kind]. Scope stays `kind`, the cache prefix
    # survives, and the manifest stops lying about its granularity.
    schema: dict                     # output contract (§P1.5)
    outcomes: frozenset[Outcome]     # closed. what this kind is allowed to return
    emits: list[EmitSpec]
    passive: list[CheckSpec]         # post_tool_call, VISIBLE to the producer
    check: CheckSpec | None          # pre_commit oracle, HIDDEN from the producer
    max_turns: int = 20              # see §P1.6: contested. the lease is the real bound.
    max_repairs: int = 1             # schema repair (§P1.5), bounded and explicit


@dataclass(frozen=True)
class Role:
    kinds: list[str]
    tiers: list[str]
    model: str                       # 'anthropic/claude-...' — provider namespaced
    effort: str                      # REQUIRED, no default (rules 72, 107)
    provider_settings: ProviderSettings   # typed, per-adapter. resolved params enter
                                          # the pin, never the abstract level (rule 134)
    jig: Jig
    lease_ttl: timedelta
    max_parallel: int
    max_children: int
    gate: str | None                 # 'depth <= 1'


class SplitRejected(Exception):  ...   # emit-time gate. classified, never a bare assert.
class StaleWriter(Exception):    ...
class ReplayMiss(Exception):     ...


# ══════════════════════════════════════════════════════════════════════
# 2. Prompt assembly.  Harness-owned.  Jigs contribute layers 0–3 only.
#    Layer order is load-bearing twice: cache prefix and attention (§P5.1).
#    Blocks stay BLOCKS all the way to the wire — see build_request.
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Block:
    layer: int
    scope: str                       # role|house|kind|run|card|attempt — §P5.1's column
    text: str

STABLE = {"role", "house", "kind", "run"}   # cacheable across cards


def render(role, task, deps, orientation, last_attempt) -> list[Block]:
    j = role.jig
    b = [
        Block(0, "role",    j.system),                       # + the outcome enum, verbatim
        Block(1, "house",   j.preamble),
        Block(2, "kind",    load_skills(SKILLS[task.kind])),   # ← by KIND, not by jig
        Block(3, "role",    tool_schemas_text(j.tools)),
        Block(8, "kind",    check_definitions(task.kind)),   # ← MOVED UP. see note 1 at foot.
        Block(4, "run",     orientation + constraints_verbatim(task.root_id)),
        Block(5, "card",    card(task)),
        Block(6, "card",    dep_summaries(deps)),
        Block(7, "attempt", last_attempt_output(last_attempt)),   # '' when attempts == 0
    ]

    # Static invariant, milliseconds, high value: the stable prefix must be
    # contiguous, or provider-side prefix caching buys nothing.
    first_variable = next(i for i, x in enumerate(b) if x.scope not in STABLE)
    if not all(x.scope in STABLE for x in b[:first_variable]):
        raise HarnessBug("cacheable prefix is not contiguous")
    return b


# ── §Skills ───────────────────────────────────────────────────────────
# THE RULE:
#     Layer 2 is not what THIS TASK needs.
#     It is what EVERY CARD OF THIS KIND needs.
#     Anything narrower is retrieval.
#
# The cost of a broad set is not tokens. Layer 2 is kind-scoped, so the cache
# amortises the price. The cost is R50: telling a model where to look makes it
# look there and marginally less elsewhere, so a broad set may degrade the cards
# it was NOT written for while every cost metric looks fine.
#
# Selection is not the fix. §P5.1: nothing computes the set, because a chooser
# is core §3.4's deleted router returning. It would also collapse the cache
# prefix — a card-scoped layer 2 pushes layers 3 and 8 out of the stable region
# behind it, losing caching on tools and check definitions to save tokens that
# were already amortised.
#
# Three legitimate levers, in the order to reach for them:
#   1. RETRIEVAL. Demote the task-specific skill to layer 6 with a named risk.
#      Triggered by a property of the CARD (touch set intersecting the store),
#      never by a model. If you cannot state the trigger as a card property,
#      it stays a skill.
#   2. MORE KINDS. execute_db / execute_pure, each minimal, each static and
#      hashable. Premature at twelve cards: halving a kind's population halves
#      its cache amortisation. Keep for when bifurcation proves structural.
#   3. SMALLER SETS. Nothing to cut once you are at one or two.
#
# skills.yaml on day one — empty, and correct. Skills arrive from Phase B, each
# paired with the RED case that motivated it, which assigns its kind, supplies
# its ablation test, and makes it removable. Without the pairing a corpus grows
# by accretion and nothing records what any file was for.
#
#     execute: []
#     verify:  []
#     split:   []
#
# More than one per kind is fine. The discipline is per-skill, never a count:
# does this one have a RED case, and does the ablation still justify it.
# verify's set stays shortest (§P5.1).


def load_skills(names: list[str]) -> str:
    """Concatenate skills/<name>.md. Both skills.yaml's hash and each file's
       hash enter config_hash — that is what makes `what did this card see`
       answerable from the ledger."""
    return "\n\n".join(read(f"skills/{n}.md") for n in names)


def card(task) -> str:
    """NOTE what is absent: the attempt budget.

    v2 passed `attempt N of M`. That is the wrong half of the retry story —
    it invites budget-gaming and last-attempt behaviour change, while
    withholding the thing that helps. The useful half is layer 7."""
    return f"""
    YOUR CARD
    intent:         {task.intent}
    contract:       {task.contract}
    ownership:      {task.touch_set}
    interfaces:     {task.interfaces}
    check_spec:     {task.check_spec}
    open_questions: {task.open_questions}   # what your splitter knew it left open
    """


def last_attempt_output(last) -> str:
    if last is None:
        return ""
    return f"""
    THE PREVIOUS ATTEMPT FAILED. Read this before editing anything.
    failure_class: {last.failure_class}
    checks:
    {truncate(last.check_output, N)}
    """


def dep_summaries(deps) -> str:
    """Layer 6. SUMMARIES, not bodies (§P9.4).

    A card that reads its parent's full diff is a card doing its parent's job
    again — and the window would not survive it. Each parent contributes ~100
    words plus a content-store ref the child may retrieve IF it can cite a
    named risk (§P5.2), which makes `how often do cards need the body` a query.

    Every dep here is `done`. ADR-0006 guarantees it at claim time, so this
    renderer never has to describe work that did not happen.

    Renders per parent:
        Exposes:  the interface. this is what makes the edge REAL — a parent
                  exposing nothing the child consumes is the emit-time gate
                  above firing.
        decided:  §4.2's field, the counterpart to open_questions going IN.
                  The set difference is a mechanical drift detector needing
                  no model call — the only R25 detector that does not depend
                  on the drifting card noticing its own drift.
        full:     a REF, not the content.

    Absent, deliberately: attempt counts, prior failures, parent state beyond
    [done]. Same reason the card no longer carries its own attempt budget."""
    return "\n".join(
        f"""
  {d.id}  {d.slug}                          [done]
    {d.summary}
    Exposes: {d.interfaces}
    decided: {d.decided}
    full:    {d.result_ref}    (retrieve only with a named risk)"""
        for d in deps
    )


# ══════════════════════════════════════════════════════════════════════
# 3. The provider port.  Neutral, typed, one method.  ADR-0005.
#
#    THE RULE: normalize the envelope, never hash the envelope.
#    Canonical types above the port; provider-native bytes below it;
#    the cache key taken over the BYTES.
# ══════════════════════════════════════════════════════════════════════

class Model(Protocol):
    def complete(self, req: Request) -> Response: ...


@dataclass(frozen=True)
class Request:                       # canonical. no provider vocabulary in here.
    blocks: list[Block]              # NOT a joined string — breakpoints need structure
    tools: list[dict]
    model: str
    effort: str
    settings: ProviderSettings


class AnthropicAdapter:
    """Owns: layer→message mapping, cache_control breakpoints, tool schema
       shape, stop-reason and exception mapping into FailureClass."""

    def build(self, req: Request) -> tuple[bytes, dict]:
        system = [as_content_block(b) for b in req.blocks if b.scope in STABLE]
        system[-1]["cache_control"] = {"type": "ephemeral"}    # ← the whole point of
                                                               #   the prefix ordering
        user = [as_content_block(b) for b in req.blocks if b.scope not in STABLE]
        body = {"system": system, "messages": [{"role": "user", "content": user}], ...}
        return canonical_bytes(body), body

    def complete(self, req):
        wire, body = self.build(req)
        try:
            return to_canonical(provider.post(body))
        except ProviderError as e:
            raise HarnessFailure(self.classify(e)) from e

    def identity(self) -> str:
        return f"anthropic-adapter@{ADAPTER_VERSION}"   # enters kind_hash


class CachedModel:
    """A cache-backed implementation OF the port, wrapping the real adapter —
       not a wrapper AROUND it. A path that bypassed the cache would have to
       bypass the port, which the runner has no way to do (§C8)."""

    def __init__(self, inner: Model, mode: str):
        self.inner, self.mode = inner, mode          # 'live' | 'replay'

    def complete(self, req: Request) -> Response:
        wire, _ = self.inner.build(req)              # bytes we are ABOUT to send
        key = sha256(wire + self.inner.identity().encode())
        # P1-24, restated: the key is computable BEFORE dispatch, and it is
        # taken over what the adapter built — not over `req`. A recording
        # proxy asserts these agree; see the kept test.
        if hit := cache.get(key):
            return hit
        if self.mode == "replay":
            raise ReplayMiss(key)                    # Gate A asserts zero outbound
        resp = self.inner.complete(req)
        cache.put(key, resp)                         # tokens, cost recorded here
        return resp


# ══════════════════════════════════════════════════════════════════════
# 4. Tool dispatch.  Five checks, fixed order, then normalize.
# ══════════════════════════════════════════════════════════════════════

def dispatch_tool(task, attempt, role, call) -> str:
    t = TOOLS.get(call.name)

    # 1 SCOPE — cheapest, most absolute. Not in the role's list => never in the
    #           schema either, so this branch should be unreachable. Alarm if hit.
    if call.name not in role.jig.tools:
        return audit_deny(task, attempt, call, "out_of_scope")
    # 2 VALIDATION — server-side, always. Before quota, so a malformed retry
    #                loop can't exhaust a well-behaved card's budget.
    if not validates(call.args, t.schema):
        return audit_deny(task, attempt, call, "invalid_args")
    # 3 QUOTA — keyed (task, ATTEMPT, tool). v2 keyed on task alone, so attempt 2
    #           inherited attempt 1's exhausted budget and failed early for the
    #           wrong reason. A fresh attempt is a fresh workspace; make it a
    #           fresh budget too.
    if not quota.take(task.id, attempt, call.name):
        return audit_deny(task, attempt, call, "quota")
    # 4 SIDE-EFFECT class
    if not side_effect_permitted(t.side_effect, role, task):
        return audit_deny(task, attempt, call, "side_effect")
    # 5 APPROVAL — rare, bounded, MUST time out.
    if needs_approval(t, call) and not approval.wait(task, call, timeout=...):
        raise NeedsApproval(call)

    raw = t.fn(**call.args)

    # NORMALIZE before the output enters the message list. Without it,
    # list_dir ordering / pytest timings / absolute paths change turn N+1's
    # cache key and replay dies at the SECOND model call — presenting as a
    # cache miss you would blame on the model. Non-optional at the type level.
    out = t.normalize(raw)

    for spec in role.jig.passive:     # welded to the write, VISIBLE by design
        out += "\n" + CHECKS[spec.type].run(spec, task, best_effort=True)

    audit(task, attempt, call, decision="allowed", args_digest=sha256(call.args))
    return out


# ══════════════════════════════════════════════════════════════════════
# 5. The runner.  Identical for split, execute, verify, judge, integrate.
# ══════════════════════════════════════════════════════════════════════

def run_jig(role, task, attempt) -> JigResult:
    j = role.jig
    deps = ledger.dependency_summaries(task)          # summaries, not bodies
    blocks = render(role, task, deps,
                    orientation=run_orientation(task.root_id),
                    last_attempt=ledger.last_attempt(task) if attempt > 0 else None)

    prompt_ref = content.put(join_for_audit(blocks))  # store what the model SAW
    req = Request(blocks=blocks, tools=[TOOLS[n].schema for n in j.tools],
                  model=role.model, effort=role.effort, settings=role.provider_settings)

    result = _turn_loop(role, task, attempt, req, prompt_ref)
    if result.outcome is not Outcome.OK and result.outcome is not Outcome.EXPANDED:
        return result                                  # refusals skip the oracle

    # The oracle. Fresh container, spec mounted from a ref the working
    # container never had. FOUR states, never two.
    return replace(result, check=run_oracle(j.check, task) if j.check
                                 else CheckResult("not_applicable"))


def _turn_loop(role, task, attempt, req, prompt_ref) -> JigResult:
    j, repairs, messages = role.jig, 0, []

    for turn in range(j.max_turns):
        resp = model.complete(replace(req, blocks=req.blocks + as_blocks(messages)))

        if resp.tool_calls:
            messages.append(resp.as_assistant())
            for c in resp.tool_calls:
                messages.append(tool_result(c, dispatch_tool(task, attempt, role, c)))
            continue

        payload = parse(resp.text, j.schema)
        if payload is None:
            # Schema repair (§P1.5): bounded, explicit, one more turn — NOT a
            # fresh attempt. v2 had no repair path at all.
            if repairs < j.max_repairs:
                repairs += 1
                messages += [resp.as_assistant(), schema_repair_prompt(j.schema)]
                continue
            return JigResult(Outcome.SCHEMA_VIOLATION, prompt_ref=prompt_ref,
                             failure_class=FailureClass.MALFORMED_OUTPUT)

        return _classify_payload(j, payload, resp, role, prompt_ref)

    # Turn cap. Its OWN outcome — v2 folded this into `misclassified`, which
    # conflates "the card was the wrong shape" (→ resplit) with "we ran out of
    # turns" (→ raise the cap, or narrow the contract). Different remedies.
    # And never a success: RED-000, the SDK whose max-turns error left is_error
    # unset and turned exhaustion into a completed run.
    return JigResult(Outcome.EXPLORATION_CAP, prompt_ref=prompt_ref,
                     failure_class=FailureClass.TURN_LIMIT)


def _classify_payload(j, payload, resp, role, prompt_ref) -> JigResult:
    if r := payload.get("refusal"):
        # The model NAMES a reason; the harness decides whether that reason
        # exists. v2 put the raw string straight into the ledger's outcome
        # column, so 'blocked', 'Blocked' and 'blocked_on_dep' all became
        # distinct values and every GROUP BY outcome fragmented silently.
        try:
            outcome = Outcome(r["reason"])
        except ValueError:
            return JigResult(Outcome.SCHEMA_VIOLATION, prompt_ref=prompt_ref,
                             detail=f"unknown reason {r['reason']!r}")
        if outcome not in j.outcomes:
            return JigResult(Outcome.SCHEMA_VIOLATION, prompt_ref=prompt_ref,
                             detail=f"{outcome} not permitted for kind")
        return JigResult(outcome, payload=payload, prompt_ref=prompt_ref)

    return JigResult(
        Outcome.EXPANDED if j.emits_children else Outcome.OK,
        payload=payload,
        summary=payload["summary"],       # includes `decided` — see note 3
        prompt_ref=prompt_ref,
        cost=resp.cost, tokens=(resp.tokens_in, resp.tokens_out), model=role.model,
    )


# ── §Checks ───────────────────────────────────────────────────────────
# Check definitions are LAYER 8, therefore inside config_hash — so the check
# set needs a hash, which means each check needs a pinned version.
#
# pre-commit already solved exactly this: checks declared as data, each pinned
# to a `rev`, resolved into isolated per-check environments, run over a file
# set. Steal the SHAPE for checks.yaml.
#
# Optionally steal the RUNNER for rungs 0–1 (`pre-commit run --all-files`),
# with .pre-commit-config.yaml in the WORKLOAD repo. One trap if you do: it
# caches environments outside your image, so a card's check environment can
# differ from the template's. Bake the cache dir into the image; do not mount.
#
# Rung 3 is where it stops helping. `lsp_diagnostics` needs a client driving a
# language server; for the todo prototype every rung is `command` (ruff, mypy,
# pytest) and the question does not arise.
#
# Borrow promptfoo's ASSERTION VOCABULARY — the taxonomy of deterministic vs
# model-graded checks — as input to checks.yaml's design. Skip its runner: an
# ablation here is same board, bump config_version, re-run, compare, and our
# substrate gives deterministic replay and per-attempt cost accounting that an
# external runner bypasses along with the cache and the ledger.

def run_oracle(spec, task) -> CheckResult:
    """Best-effort. A check that can crash a card is worse than no check."""
    try:
        r = CHECKS[spec.type].run(spec, task, hidden=True, container=fresh())
    except (SpawnFailure, Timeout, BrokenPipe):
        return CheckResult("unavailable")    # NOT 'passed'. See note 2.
    return CheckResult("passed" if r.ok else "failed", detail=truncate(r.detail, N))


# ══════════════════════════════════════════════════════════════════════
# 6. Emission.  Schema-driven, so roles need no code — only a manifest.
# ══════════════════════════════════════════════════════════════════════

def plan_emissions(role, task, payload) -> list[NewTask]:
    emitted = []
    for spec in role.jig.emits:            # order matters: gates see the children
        emitted += SHAPES[spec.shape](role, task, payload, spec, emitted)
    return emitted


@register(SHAPES, "children")
def shape_children(role, task, payload, spec, emitted) -> list[NewTask]:
    parent = task.id if spec.parent == "self" else task.parent_id   # verify emits SIBLINGS
    kids = [
        NewTask(
            id=child_id(parent, c),        # 't-' + hash(root_id, kind, normalized intent)
            root_id=task.root_id, parent_id=parent, caused_by=task.id,
            kind=c["kind"], tier=tier_for(c), intent=c["intent"],
            contract=c["contract"], check_spec=c["check_spec"],
            touch_set=c["touch_set"], open_questions=c.get("open_questions", []),
            deps=[resolve(d, parent) for d in c.get("deps", [])],
            state="awaiting_review" if gated(role, parent) else "pending",
            config_version=task.config_version, config_hash=task.config_hash,
        )
        for c in payload["children"]
    ]
    # Emit-time gates. RAISED, not asserted: `python -O` strips asserts, and an
    # AssertionError falls into the generic handler while the collision check
    # three lines down gets classified properly. Same gate class, one fate.
    if not 2 <= len(kids) <= role.max_children:
        raise SplitRejected("fan_out", len(kids))
    if not all(k.check_spec for k in kids):
        raise SplitRejected("missing_check_spec")      # crude, never false-rejects
    reject_if_touch_sets_collide(kids)     # false independence
    reject_if_edge_carries_nothing(kids)   # false dependence
    return kids


def reject_if_edge_carries_nothing(kids):
    """The DUAL of the collision check, and the gate that was missing.

    reject_if_touch_sets_collide catches FALSE INDEPENDENCE: two cards claiming
    they can run together when they would collide.

    Nothing caught FALSE DEPENDENCE: a card claiming it must wait when no data
    crosses. A splitter that emits B.deps=[A], C.deps=[B] because that is the
    order it thought of them has serialized three independent cards, and the
    board will faithfully execute the mistake on every run forever. The
    predicate cannot catch it — a dep is a dep.

    The test: does the child actually READ the parent's output? The card shape
    already carries the field, so require every dep to name what it consumes.
    One pass, never false-rejects, fails loudly at split rather than silently
    costing wall-clock thereafter. (R-new-4)

    Detector for the register: dep count vs consumes count, per card."""
    for k in kids:
        for d in k.deps:
            if not k.consumes.get(d):      # names an interface the parent exposes
                raise SplitRejected("edge_carries_no_data", k.id, d)


def reject_if_touch_sets_collide(kids):
    """One set-intersection. Converts the most expensive late failure
       (integrate-time conflict) into an emit-time rejection."""
    for a, b in combinations(kids, 2):
        if set(a.touch_set) & set(b.touch_set) and not depends(a, b):
            raise SplitRejected("touch_set_collision", a.id, b.id)


# ══════════════════════════════════════════════════════════════════════
# 7. Commit.  One transaction, fenced.
# ══════════════════════════════════════════════════════════════════════

TERMINAL_STATE = {
    Outcome.OK: "done", Outcome.EXPANDED: "done",
    Outcome.BLOCKED: "blocked", Outcome.MISCLASSIFIED: "needs_review",
    Outcome.EXPLORATION_CAP: "failed", Outcome.SCHEMA_VIOLATION: "failed",
    Outcome.REFUSED: "refused",
}


def commit(task, attempt, result: JigResult, new_tasks):
    # v2 hardcoded state='done' regardless of outcome, so a schema_violation
    # committed as a success.
    with db.tx():
        n = db.exec("""
            UPDATE tasks SET state=%s, outcome=%s, result_ref=%s, result_summary=%s,
                             check_result=%s, prompt_ref=%s, model_used=%s,
                             tokens_in=%s, tokens_out=%s, cost_usd=%s, updated_at=now()
             WHERE id=%s AND lease_holder=%s AND attempts=%s
        """, TERMINAL_STATE[result.outcome], result.outcome, ...,
             task.id, worker_id, attempt)          # ← attempt is the fencing token
        if n == 0:
            raise StaleWriter(task.id)             # a re-claimed zombie loses here

        if new_tasks:
            db.exec("INSERT INTO tasks (...) VALUES ... ON CONFLICT (id) DO NOTHING", new_tasks)
            db.exec("INSERT INTO outbox (task_id, kind) SELECT id, kind FROM ...", new_tasks)


# ══════════════════════════════════════════════════════════════════════
# 8. Worker loop.  Not an actor. No address, no mailbox, no identity.
# ══════════════════════════════════════════════════════════════════════

def worker(role):
    while not draining:
        claim = ledger.claim(kinds=role.kinds, tiers=role.tiers,
                             holder=worker_id, ttl=role.lease_ttl)
        if claim is None:
            wait_for_notify_or_timeout(role.poll_interval); continue

        task, attempt = claim.task, claim.attempts   # fencing token, returned at claim time
        hb, committed = spawn_background(heartbeat, task, attempt, role.lease_ttl), False
        try:
            run_hooks("post_claim", task)            # workspace reset, template clone
            result = run_jig(role, task, attempt)
            new_tasks = plan_emissions(role, task, result.payload) if result.payload else []
            run_hooks("pre_commit", task, result)
            commit(task, attempt, result, new_tasks)
            committed = True
        except StaleWriter:
            pass                                     # newer claim owns it; drop ours silently
        except SplitRejected as e:
            ledger.fail(task, attempt, FailureClass.MALFORMED_OUTPUT, detail=e)
            committed = True                         # our own row, fenced inside ledger.fail
        except HarnessFailure as e:
            # FREE_RETRY classes resume WITHOUT consuming an attempt (§C10).
            ledger.fail(task, attempt, e.failure_class,
                        consume=e.failure_class not in FREE_RETRY)
            committed = True
        except Exception as e:
            ledger.fail(task, attempt, FailureClass.HARNESS_BUG, detail=e)
            committed = True
        finally:
            hb.stop()
            # v2 ran post_commit for a zombie whose work was discarded. Cleanup
            # for a row we do not own is at best wasted and at worst destructive.
            if committed:
                run_hooks("post_commit", task)

    # SIGTERM: stop claiming, finish if it fits the grace period, else release
    # the lease NOW rather than making the reaper wait out the TTL.


def heartbeat(task, attempt, ttl):
    """Background task, NOT inside the model call — a hung connection must stop
       the heartbeat rather than mask the hang. deadline_at is never extended;
       that is the point of two clocks."""
    while not stopped:
        db.exec("""UPDATE tasks SET lease_expires_at=now()+%s, last_heartbeat_at=now()
                    WHERE id=%s AND lease_holder=%s AND attempts=%s AND state='leased'""",
                ttl, task.id, worker_id, attempt)
        sleep(ttl / 3)


# ══════════════════════════════════════════════════════════════════════
# What changed in v4 (registries)
# ══════════════════════════════════════════════════════════════════════
#
#   · SKILLS is its own registry, keyed by KIND, read as SKILLS[task.kind].
#     v3 hung it off the Jig, which broke for any role serving two kinds.
#   · Jig.system became system_ref, so two kinds can share one jig body and
#     differ only in their skill set without inflating §P2's jig count.
#   · ToolImpl.schema is DERIVED from fn via TypeAdapter, not hand-written.
#   · The six real tools are enumerated, with their normalizers, and §Tools
#     records why this registry is not MCP.
#   · HOOKS -> pluggy, with entry-point discovery explicitly not called.
#   · §Checks records pre-commit as the shape for checks.yaml.
#   · canonical_bytes is an RFC 8785 import, pinned, not a hand-rolled
#     helper. (R-new-6)
#   · SATISFIES_DEP = {"done"} — ADR-0006.
#   · reject_if_edge_carries_nothing — the dual of the collision gate.
#     (R-new-4)
#   · dep_summaries sketched: Exposes / decided / full-as-ref, and nothing
#     about the parent's attempts.
#
# Still elided, and now conspicuously: the transitive-stall query that
# ADR-0006 requires — cards pending with a blocked or failed ancestor.
# It lives in the ledger, not here, but the decision is only safe with it.
#
# ══════════════════════════════════════════════════════════════════════
# What changed from the v2 sketch
# ══════════════════════════════════════════════════════════════════════
#
# Correctness
#   · cache key moved BELOW the port, taken over the adapter's wire bytes
#     plus adapter identity. v2 hashed `messages` + schema digests — the
#     canonical form, not what the provider received. That is exactly the
#     false positive P1-24 exists to catch.
#   · blocks survive to the wire. v2 asserted a contiguous cacheable prefix
#     and then join()ed it into one user message, discarding the structure
#     that made the ordering worth computing. Now: stable blocks become the
#     system array with a cache_control breakpoint on the last one.
#   · layer stack renumbered to §P5.1. Layer 7 is the previous attempt's
#     check output; v2 had no layer for it.
#   · the attempt budget left the card. Layer 7 replaces it.
#   · exploration_cap is its own outcome and its own failure_class.
#   · outcomes validated against a closed enum AND against the kind's
#     permitted set. v2 wrote a model-authored string to the ledger.
#   · emit-time gates raise SplitRejected instead of asserting.
#   · quota keyed on (task, attempt, tool).
#   · commit maps outcome → state.
#   · StaleWriter no longer runs post_commit hooks.
#   · schema repair path added, bounded by max_repairs.
#   · effort + typed ProviderSettings replace a bare temperature.
#
# Kept, unchanged, because they were right
#   · normalize as a REQUIRED field on ToolImpl
#   · CheckResult('unavailable') as a fourth state
#   · fencing on `attempts` in the UPDATE's WHERE clause
#   · heartbeat outside the model call; deadline_at never extended
#   · open_questions in, `decided` back
#   · emits-as-data
#
# Removed pending confirmation
#   · memory.recall / notes / note_ids. I cannot find a memory system in v3;
#     §P5.2 is named-risk retrieval instead. If it was deleted, this was
#     drift. If it survived, it is the one place state lives outside the
#     board, and `sorted(note_ids)` in the key was an honest admission that
#     recall drift silently breaks replay. Decide before restoring.
#
# ── Three decisions worth arguing with ────────────────────────────────
#
# 1. Layer 8 moved up, next to layers 2–3.
#    §P5.1 lists check definitions LAST, at kind scope. But a kind-scoped
#    layer sitting behind card- and attempt-scoped ones can never be in the
#    cached prefix — its scope is a lie about its cost. Either it moves up
#    (done here) or the table should say `card`. This is a real conflict
#    with the doc, not a transcription slip; §P5.1 needs an in-place edit
#    either way. The attention argument may cut the other way — checks read
#    last may land harder — in which case keep the order and fix the scope
#    column. That is a jig-content question and it is measurable.
#
# 2. `emits` as data. The bet that split/verify/judge/execute differ only in
#    manifest. shape_children already carries one conditional for verify's
#    sibling emission. Two conditionals is a pattern, and the bet is wrong —
#    better to find that at three jigs than at eight.
#
# 3. CheckResult('unavailable'). Recording it as a pass gives §C11 an
#    unlisted sibling: the check that never ran. Its symptom is also
#    everything working, and the mutation probe will not catch it — the
#    probe tests the suite, not the plumbing that invokes it.
#    Metric: cards committed with a non-'passed' oracle, by kind.
#
# ── New rule candidate ────────────────────────────────────────────────
#
# R-new-5: every tool's output is normalised before it enters the message
# list. Unnormalised output makes turn N+1's cache key a function of
# directory ordering and wall-clock timings; replay then dies at the second
# model call and presents as a cache miss you would blame on the model.
# This is not in core or policy and it belongs in one of them — arguably a
# bigger determinism threat than sampling, which §C8 already handles.
#
# Elided: the claim query and readiness predicate (§C5 — the ledger, not the
# jig); the reaper; reset-from-a-point; digest SQL.
