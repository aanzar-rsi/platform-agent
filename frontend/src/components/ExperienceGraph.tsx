import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  ExperienceChunk,
  ExperienceGraphLink,
  ExperienceGraphNode,
} from "@/lib/api";

type LayoutNode = ExperienceGraphNode & {
  x: number;
  y: number;
  radius: number;
  homeX: number;
  homeY: number;
  labelAngle?: number;
};

type LayoutLink = {
  sourceId: string;
  targetId: string;
  weight: number;
  kind: ExperienceGraphLink["kind"];
};

const OUTCOME_COLOR: Record<string, string> = {
  success: "#3d9b7a",
  failure: "#c45c4a",
  unexpected: "#fbe232",
  unknown: "#737373",
};

function outcomeColor(outcome?: string) {
  return OUTCOME_COLOR[outcome || "unknown"] || OUTCOME_COLOR.unknown;
}

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

interface ExperienceGraphProps {
  nodes: ExperienceGraphNode[];
  links: ExperienceGraphLink[];
  chunks: ExperienceChunk[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  outcomeFilter: Set<string>;
  search: string;
}

export default function ExperienceGraph({
  nodes,
  links,
  chunks,
  selectedId,
  onSelect,
  outcomeFilter,
  search,
}: ExperienceGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layoutRef = useRef<{ nodes: LayoutNode[]; links: LayoutLink[] }>({
    nodes: [],
    links: [],
  });
  const rafRef = useRef<number>(0);
  const dragRef = useRef<{ id: string; ox: number; oy: number } | null>(null);
  const hoverRef = useRef<string | null>(null);
  const selectedRef = useRef(selectedId);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 560 });
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });

  selectedRef.current = selectedId;

  const chunkMap = useMemo(() => {
    const m = new Map<string, ExperienceChunk>();
    for (const c of chunks) m.set(c.id, c);
    return m;
  }, [chunks]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const tools = nodes
      .filter((n) => n.kind === "tool")
      .slice()
      .sort((a, b) => (b.count || 0) - (a.count || 0) || a.label.localeCompare(b.label));

    const expsByTool = new Map<string, ExperienceGraphNode[]>();
    for (const n of nodes) {
      if (n.kind !== "experience") continue;
      const outcome = n.outcome || "unknown";
      if (!outcomeFilter.has(outcome)) continue;
      if (q) {
        const chunk = chunkMap.get(n.id);
        const hay = [
          n.label,
          n.tool,
          chunk?.advice,
          chunk?.metadata?.user_query,
          chunk?.metadata?.learning,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        if (!hay.includes(q) && !(n.tool || "").toLowerCase().includes(q)) continue;
      }
      const key = n.tool || "unknown";
      if (!expsByTool.has(key)) expsByTool.set(key, []);
      expsByTool.get(key)!.push(n);
    }

    const visibleTools = tools.filter((t) => {
      if (!q) return (expsByTool.get(t.label)?.length || 0) > 0 || (t.count || 0) > 0;
      if (t.label.toLowerCase().includes(q)) return true;
      return (expsByTool.get(t.label)?.length || 0) > 0;
    });

    return { tools: visibleTools, expsByTool };
  }, [nodes, outcomeFilter, search, chunkMap]);

  const focusTool = useMemo(() => {
    if (!selectedId) return null;
    if (selectedId.startsWith("tool:")) return selectedId.slice(5);
    const exp = nodes.find((n) => n.id === selectedId);
    return exp?.tool || null;
  }, [selectedId, nodes]);

  // Structured layout — tools on rings, experiences only around focused hub
  useEffect(() => {
    const w = size.w;
    const h = size.h;
    const cx = w / 2;
    const cy = h / 2;
    const { tools, expsByTool } = filtered;
    const n = tools.length;
    const layoutNodes: LayoutNode[] = [];

    // Even spacing on 1–2 rings based on count
    const useTwoRings = n > 16;
    const outerCount = useTwoRings ? Math.ceil(n * 0.62) : n;
    const innerCount = n - outerCount;
    const pad = 70;
    const maxR = Math.min(w, h) / 2 - pad;
    const outerR = maxR * (useTwoRings ? 0.92 : 0.78);
    const innerR = maxR * 0.48;

    tools.forEach((tool, i) => {
      let ring: number;
      let idx: number;
      let count: number;
      if (!useTwoRings) {
        ring = outerR;
        idx = i;
        count = n;
      } else if (i < outerCount) {
        ring = outerR;
        idx = i;
        count = outerCount;
      } else {
        ring = innerR;
        idx = i - outerCount;
        count = Math.max(innerCount, 1);
      }
      const angle = (idx / count) * Math.PI * 2 - Math.PI / 2;
      const x = cx + Math.cos(angle) * ring;
      const y = cy + Math.sin(angle) * ring;
      const expCount = expsByTool.get(tool.label)?.length ?? tool.count ?? 0;
      layoutNodes.push({
        ...tool,
        x,
        y,
        homeX: x,
        homeY: y,
        radius: clamp(11 + Math.sqrt(expCount) * 2.2, 12, 22),
        labelAngle: angle,
      });
    });

    const toolPos = new Map(layoutNodes.map((n) => [n.label, n]));

    // Experiences: only for focused tool, arranged in a clean arc/orbit
    if (focusTool) {
      const parent = toolPos.get(focusTool);
      const list = (expsByTool.get(focusTool) || []).slice(0, 12);
      if (parent && list.length) {
        const outward = Math.atan2(parent.y - cy, parent.x - cx);
        const span = Math.min(Math.PI * 1.1, 0.35 + list.length * 0.14);
        const start = outward - span / 2;
        const orbitR = parent.radius + 56;

        list.forEach((exp, i) => {
          const t = list.length === 1 ? 0.5 : i / (list.length - 1);
          const angle = start + span * t;
          const x = parent.x + Math.cos(angle) * orbitR;
          const y = parent.y + Math.sin(angle) * orbitR;
          layoutNodes.push({
            ...exp,
            x,
            y,
            homeX: x,
            homeY: y,
            radius: 7,
            labelAngle: angle,
          });
        });
      }
    }

    const idSet = new Set(layoutNodes.map((n) => n.id));
    const layoutLinks: LayoutLink[] = [];

    // Only tool→tool transitions (no belongs spaghetti). Prefer edges among visible tools.
    for (const l of links) {
      if (l.kind !== "transition") continue;
      if (!idSet.has(l.source) || !idSet.has(l.target)) continue;
      layoutLinks.push({
        sourceId: l.source,
        targetId: l.target,
        weight: l.weight,
        kind: l.kind,
      });
    }

    // Soft spokes from focused tool to its experiences
    if (focusTool) {
      const parentId = `tool:${focusTool}`;
      for (const n of layoutNodes) {
        if (n.kind === "experience") {
          layoutLinks.push({
            sourceId: parentId,
            targetId: n.id,
            weight: 1,
            kind: "belongs",
          });
        }
      }
    }

    // Animate from previous positions when possible
    const prev = new Map(layoutRef.current.nodes.map((n) => [n.id, n]));
    for (const n of layoutNodes) {
      const old = prev.get(n.id);
      if (old) {
        n.x = old.x;
        n.y = old.y;
      } else if (n.kind === "experience" && focusTool) {
        const parent = toolPos.get(focusTool);
        if (parent) {
          n.x = parent.x;
          n.y = parent.y;
        }
      }
    }

    layoutRef.current = { nodes: layoutNodes, links: layoutLinks };
  }, [filtered, links, size.w, size.h, focusTool]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ w: Math.max(320, width), h: Math.max(400, height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Render loop — ease toward home positions (no chaotic forces)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const tick = () => {
      if (!running) return;
      const { nodes: lns, links: lls } = layoutRef.current;
      const w = size.w;
      const h = size.h;
      const cx = w / 2;
      const cy = h / 2;
      const sel = selectedRef.current;
      const hov = hoverRef.current;
      const nodeMap = new Map(lns.map((n) => [n.id, n]));

      for (const n of lns) {
        if (dragRef.current?.id === n.id) continue;
        n.x = lerp(n.x, n.homeX, 0.12);
        n.y = lerp(n.y, n.homeY, 0.12);
      }

      const dpr = window.devicePixelRatio || 1;
      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);

      const bg = ctx.createRadialGradient(cx, cy, 30, cx, cy, Math.max(w, h) * 0.72);
      bg.addColorStop(0, "#171717");
      bg.addColorStop(0.55, "#101010");
      bg.addColorStop(1, "#010101");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      // Subtle guide rings
      ctx.strokeStyle = "rgba(201, 139, 39, 0.06)";
      ctx.lineWidth = 1;
      for (const r of [0.48, 0.78, 0.92]) {
        ctx.beginPath();
        ctx.arc(cx, cy, (Math.min(w, h) / 2 - 70) * r, 0, Math.PI * 2);
        ctx.stroke();
      }

      ctx.fillStyle = "rgba(251, 226, 50, 0.035)";
      for (let gx = 28; gx < w; gx += 32) {
        for (let gy = 28; gy < h; gy += 32) {
          ctx.beginPath();
          ctx.arc(gx, gy, 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      const { x: tx, y: ty, k } = transformRef.current;
      ctx.save();
      ctx.translate(tx, ty);
      ctx.scale(k, k);

      const focusLabel =
        sel?.startsWith("tool:") ? sel.slice(5)
        : sel?.startsWith("exp_") ? nodeMap.get(sel)?.tool
        : null;

      // Transition edges — thin, quiet unless related to focus
      for (const link of lls) {
        if (link.kind !== "transition") continue;
        const a = nodeMap.get(link.sourceId);
        const b = nodeMap.get(link.targetId);
        if (!a || !b) continue;

        const related =
          !focusLabel ||
          a.label === focusLabel ||
          b.label === focusLabel;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        const mx = (a.x + b.x) / 2;
        const my = (a.y + b.y) / 2;
        // Curve toward center for a cleaner chord look
        const cpx = lerp(mx, cx, 0.35);
        const cpy = lerp(my, cy, 0.35);
        ctx.quadraticCurveTo(cpx, cpy, b.x, b.y);
        ctx.strokeStyle = related
          ? "rgba(201, 139, 39, 0.28)"
          : "rgba(201, 139, 39, 0.07)";
        ctx.lineWidth = related ? 1.4 : 0.9;
        ctx.stroke();
      }

      // Spokes to expanded experiences
      for (const link of lls) {
        if (link.kind !== "belongs") continue;
        const a = nodeMap.get(link.sourceId);
        const b = nodeMap.get(link.targetId);
        if (!a || !b) continue;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = "rgba(160, 185, 220, 0.28)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Tool nodes
      for (const n of lns) {
        if (n.kind !== "tool") continue;
        const isSel = n.id === sel || n.label === focusLabel;
        const isHov = n.id === hov;
        const dimmed = !!focusLabel && !isSel;

        if (isSel || isHov) {
          const glow = ctx.createRadialGradient(
            n.x,
            n.y,
            n.radius * 0.3,
            n.x,
            n.y,
            n.radius * 2.6,
          );
          glow.addColorStop(0, "rgba(201, 139, 39, 0.4)");
          glow.addColorStop(1, "rgba(201, 139, 39, 0)");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius * 2.6, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? "rgba(18, 35, 61, 0.5)" : "#262626";
        ctx.fill();
        ctx.strokeStyle = dimmed
          ? "rgba(201, 139, 39, 0.2)"
          : isSel
            ? "#fbe232"
            : "#fbe232";
        ctx.lineWidth = isSel ? 2.4 : 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * 0.32, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? "rgba(201, 139, 39, 0.2)" : "#fbe232";
        ctx.fill();

        // Count inside
        ctx.font = `600 9px "Segoe UI", system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = dimmed ? "rgba(251, 226, 50, 0.35)" : "#fbe232";
        ctx.fillText(String(n.count || 0), n.x, n.y);

        // Radial labels outside the node
        const angle = n.labelAngle ?? 0;
        const labelR = n.radius + 14;
        const lx = n.x + Math.cos(angle) * labelR;
        const ly = n.y + Math.sin(angle) * labelR;
        const label = n.label.length > 18 ? n.label.slice(0, 16) + "…" : n.label;
        ctx.font = `600 ${isSel || isHov ? 11 : 10}px "Segoe UI", system-ui, sans-serif`;
        ctx.fillStyle = dimmed ? "rgba(220, 230, 245, 0.28)" : "#f5f5f5";
        const cos = Math.cos(angle);
        ctx.textAlign = cos > 0.25 ? "left" : cos < -0.25 ? "right" : "center";
        ctx.textBaseline = "middle";
        ctx.fillText(label, lx, ly);
      }

      // Experience satellites (focused only)
      for (const n of lns) {
        if (n.kind !== "experience") continue;
        const isSel = n.id === sel;
        const isHov = n.id === hov;
        const color = outcomeColor(n.outcome);

        if (isSel || isHov) {
          const glow = ctx.createRadialGradient(n.x, n.y, 2, n.x, n.y, 20);
          glow.addColorStop(0, color + "aa");
          glow.addColorStop(1, color + "00");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, 20, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, isSel ? 8 : 6.5, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = isSel ? "#fff" : "rgba(255,255,255,0.4)";
        ctx.lineWidth = isSel ? 2 : 1;
        ctx.stroke();
      }

      ctx.restore();
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      running = false;
      cancelAnimationFrame(rafRef.current);
    };
  }, [size.w, size.h]);

  const screenToWorld = useCallback((sx: number, sy: number) => {
    const { x, y, k } = transformRef.current;
    return { x: (sx - x) / k, y: (sy - y) / k };
  }, []);

  const hitTest = useCallback(
    (sx: number, sy: number) => {
      const { x, y } = screenToWorld(sx, sy);
      const { nodes: lns } = layoutRef.current;
      let best: LayoutNode | null = null;
      let bestD = Infinity;
      for (const n of lns) {
        const d = Math.hypot(n.x - x, n.y - y);
        const hitR = n.radius + (n.kind === "tool" ? 6 : 5);
        if (d <= hitR && d < bestD) {
          best = n;
          bestD = d;
        }
      }
      return best;
    },
    [screenToWorld],
  );

  const onPointerDown = (e: React.PointerEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;
    const hit = hitTest(sx, sy);
    if (hit) {
      dragRef.current = { id: hit.id, ox: sx, oy: sy };
      onSelect(hit.id);
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    } else {
      onSelect(null);
      dragRef.current = { id: "__pan__", ox: sx, oy: sy };
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    if (dragRef.current) {
      if (dragRef.current.id === "__pan__") {
        const dx = sx - dragRef.current.ox;
        const dy = sy - dragRef.current.oy;
        dragRef.current.ox = sx;
        dragRef.current.oy = sy;
        const next = {
          ...transformRef.current,
          x: transformRef.current.x + dx,
          y: transformRef.current.y + dy,
        };
        transformRef.current = next;
        setTransform(next);
      } else {
        const world = screenToWorld(sx, sy);
        const n = layoutRef.current.nodes.find((x) => x.id === dragRef.current!.id);
        if (n) {
          n.x = world.x;
          n.y = world.y;
          n.homeX = world.x;
          n.homeY = world.y;
        }
      }
      return;
    }

    const hit = hitTest(sx, sy);
    const id = hit?.id ?? null;
    if (id !== hoverRef.current) {
      hoverRef.current = id;
      setHoverId(id);
    }
  };

  const onPointerUp = () => {
    dragRef.current = null;
  };

  // Non-passive wheel so zoom doesn't scroll the page
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const rect = canvas.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;
      const { x, y, k } = transformRef.current;
      const nextK = clamp(k * (e.deltaY > 0 ? 0.92 : 1.08), 0.45, 2.8);
      const wx = (sx - x) / k;
      const wy = (sy - y) / k;
      const next = { k: nextK, x: sx - wx * nextK, y: sy - wy * nextK };
      transformRef.current = next;
      setTransform(next);
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, []);

  const hoverChunk =
    hoverId && hoverId.startsWith("exp_") ? chunkMap.get(hoverId) : null;
  const hoverTool =
    hoverId && hoverId.startsWith("tool:")
      ? nodes.find((n) => n.id === hoverId)
      : null;

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[480px] rounded-2xl overflow-hidden border border-[#171717]/15 shadow-2xl overscroll-none"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing touch-none"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={() => {
          hoverRef.current = null;
          setHoverId(null);
          dragRef.current = null;
        }}
      />

      <div className="absolute left-4 bottom-4 flex flex-wrap gap-3 rounded-xl bg-[#101010]/85 backdrop-blur-md border border-white/10 px-3 py-2 text-[11px] text-white/80">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#fbe232] ring-2 ring-[#fbe232]/40" />
          Tool hub
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-[#3d9b7a]" />
          Success
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-[#c45c4a]" />
          Failure
        </span>
        <span className="text-white/40">· click a hub to expand experiences</span>
      </div>

      {(hoverChunk || hoverTool) && (
        <div className="pointer-events-none absolute right-4 top-4 max-w-sm rounded-xl bg-[#101010]/92 backdrop-blur-md border border-[#fbe232]/25 px-4 py-3 shadow-xl">
          {hoverTool ? (
            <>
              <div className="text-[10px] uppercase tracking-[0.16em] text-[#fbe232]/90 mb-1">
                Tool
              </div>
              <div className="text-sm font-semibold text-white">{hoverTool.label}</div>
              <div className="text-xs text-white/55 mt-1">
                {hoverTool.count} experiences · click to expand
              </div>
            </>
          ) : hoverChunk ? (
            <>
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className="text-[10px] uppercase tracking-[0.14em] px-1.5 py-0.5 rounded"
                  style={{
                    background: outcomeColor(hoverChunk.metadata?.outcome) + "33",
                    color: outcomeColor(hoverChunk.metadata?.outcome),
                  }}
                >
                  {hoverChunk.metadata?.outcome || "unknown"}
                </span>
                <span className="text-[10px] text-white/45 font-mono">
                  {hoverChunk.metadata?.observed_tool}
                </span>
              </div>
              <div className="text-xs text-white/90 leading-relaxed line-clamp-4">
                {hoverChunk.advice}
              </div>
            </>
          ) : null}
        </div>
      )}

      <div className="absolute right-4 bottom-4 text-[10px] text-white/35 font-mono">
        {Math.round(transform.k * 100)}%
      </div>
    </div>
  );
}
