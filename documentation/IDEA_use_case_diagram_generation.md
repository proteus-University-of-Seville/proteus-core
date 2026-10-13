IDEA: automatic generation of use case diagrams
===============================================

Status: **idea, not scheduled** (analysed on 2026-10-13, to be taken up in the future).

## Idea

Generate the use case diagrams of a document automatically from the model. A
`use-case-diagram` archetype would have traces to the use cases that must appear in it;
from them a PlantUML text is built and an engine turns it into an image.

The archetype already exists in the madeja profile (`use-case-diagram`, classes
`figure diagram requirement use-case-diagram`, with a `file` property) but it is orphan: it
is not used by the sample project and it is rendered through the figure template. It fits
almost as it is, adding the trace and keeping `file` as the output.

## Data available in the model

- **Use cases of the diagram**: a new trace property (e.g. `use-cases`) in the archetype.
- **Actors**: they need (almost) no declaration. They are deduced from the steps of the
  use cases and from `inherits-from`, in the same way as the participation of the system
  actors in the madeja templates. The diagram computes them from the chosen use cases.
- **Generalization between actors**: from `inherits-from`.
- **Relationships between use cases** (`include`, `extend`, generalization): not checked
  how they are modelled today in the profile. They determine how rich the diagram can be.

The PlantUML text (`actor`, `rectangle "System" { usecase ... }`, arrows) is generated in
pure Python: deterministic and testable without any engine.

## The engine

There is no PlantUML implementation in Python. The `plantuml` package of PyPI is only a
client of a remote server.

| Option | Pros | Cons |
|---|---|---|
| Remote server (plantuml.com, Kroki) | Nothing to install | The requirements leave the user's machine (confidentiality), needs network, depends on the availability of the service, unusable in CI and in corporate environments |
| Local `plantuml.jar` (`java -jar plantuml.jar -pipe -tsvg`) | Offline, private, reproducible | Needs Java (recent PlantUML versions ask for a recent one; to be checked) and, for use case diagrams, Graphviz (`dot`), except with the weaker internal "smetana" layout |
| Graphviz directly (generate DOT, run `dot`) | No Java, one small binary, full control of the look | UML actors and notation must be drawn by us |
| Own SVG layout | No dependencies | The diagrams are small, but avoiding crossings is hard; it would become our own maintenance burden |

**Recommendation**: local jar as the main engine, configured with the path to the jar (or
detected as `plantuml` in the PATH), the same pattern as the LaTeX engines. The remote
server only as an explicit option, disabled by default. Do not bundle the jar with
PROTEUS (GPL in its default variant); running it as an external process avoids licensing
problems.

## Java without a local installation

uv does not manage JVMs, but a virtual environment can contain one if a PyPI package
bundles it (from memory, to be verified before deciding):

- **`jdk4py`**: one wheel per platform (Windows, macOS, Linux) with a minimal JRE built
  with `jlink`; it exposes the path of the `java` executable. Installed like any
  dependency, no Java needed in the system. Tens of MB per platform.
- **`install-jdk`**: downloads a JDK the first time it is used; it is not in the
  environment and needs network at that moment.
- **`JPype1`**: only a Python-Java bridge, it needs an existing JVM. Does not help.

Things to verify:

1. **Modules of the minimal JRE**: PlantUML draws with `java.desktop` (AWT, ImageIO) and a
   `jlink` JRE may not include it. Test in headless mode (`-Djava.awt.headless=true`).
2. **Graphviz**: the PlantUML layout of use case diagrams uses `dot`, which is not in PyPI
   as a binary. Either use the internal "smetana" layout (pure Java, lower quality) or
   accept Graphviz as a separate dependency.
3. **The PlantUML jar** is not officially in PyPI either: download it the first time
   (verifying its hash) or bundle it (GPL, see above).
4. **Weight and scope**: a JRE in the base dependencies would make everybody's environment
   much heavier. It should be an optional extra (e.g. `uv sync --extra diagrams`) that
   PROTEUS detects.

**First step before choosing the engine**: a quick experiment with `jdk4py` + PlantUML
with smetana, to see whether the layout is good enough for small use case diagrams. If so,
the whole setup is much simpler (no Java and no Graphviz in the system).

## When to generate

- Rendering through XSLT every time: slow, needs a cache, complicates LaTeX. Not recommended.
- **Explicit "regenerate" action** (recommended): the image is written in the `assets/` of
  the project and set in the `file` property, so HTML, PDF and LaTeX treat it as any
  other figure and the templates do not change. The diagram is versioned with the project
  and readers do not need Java. A hand-drawn diagram is still possible.
- Format: SVG for HTML; for LaTeX a high resolution PNG or PDF (`\includegraphics` does
  not accept SVG without Inkscape).
- Stale diagrams: store a hash of the PlantUML text and warn in the panel when it no
  longer matches the model; never regenerate silently.

## Plan in phases

0. Experiment: `jdk4py` + PlantUML jar with smetana (see above).
1. PlantUML text generator with tests. Shown in the object or copyable (useful already for
   anyone who has PlantUML).
2. Execution of the local engine, configuration and clear error messages, "regenerate"
   action storing the file in `assets/`.
3. Stale diagram warning and LaTeX support.
4. Optional: remote server, only with explicit consent.

## Open questions

1. Is it acceptable to require Java (or Graphviz) to whoever wants to regenerate diagrams,
   given that the result is stored in the project?
2. Which relationships must the diagram show: only actor–use case, or also `include`,
   `extend` and generalization? This affects the data model of the use case.
3. Only in madeja, or also in the `basic` profile?
