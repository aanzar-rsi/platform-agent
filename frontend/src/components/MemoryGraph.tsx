import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MemoryEntry } from "@/lib/api";

type LayoutNode = {
  id: string;
  kind: "category" | "entry";
  label: string;
  category: string;
  count?: number;
  valuePreview?: string;
  x: number;
  y: number;
  homeX: number;
  homeY: number;
  radius: number;
  labelAngle?: number;
};

const CATEGORY_COLOR: Record<string, string> = {
  user_data: "#e8cc12",
  user_preferences: "#a3a3a3",
  knowledge_base: "#3d9b7a",
  interaction_history: "#fbe232",
  goals_and_intentions: "#756200",
  system_metadata: "#737373",
  behavioral_patterns: "#404040",
  user_instructions: "#9b8200",
  general: "#fbe232",
};

function categoryColor(cat: string) {
  return CATEGORY_COLOR[cat] || CATEGORY_COLOR.general;
}

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function prettyCategory(cat: string) {
  return cat.replace(/_/g, " ");
}

function valuePreview(raw: string): string {
  if (!raw || raw === "null") return "(empty)";
  if (raw.length > 48) return raw.slice(0, 46) + "…";
  return raw;
}

interface MemoryGraphProps {
  entries: MemoryEntry[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  search: string;
  categoryFilter: Set<string>;
}

export default function MemoryGraph({
  entries,
  selectedId,
  onSelect,
  search,
  categoryFilter,
}: MemoryGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layoutRef = useRef<{ nodes: LayoutNode[]; spokes: [string, string][] }>({
    nodes: [],
    spokes: [],
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

  const byCategory = useMemo(() => {
    const q = search.trim().toLowerCase();
    const map = new Map<string, MemoryEntry[]>();
    for (const e of entries) {
      const cat = e.category || "general";
      if (!categoryFilter.has(cat)) continue;
      if (q) {
        const hay = `${e.key} ${e.value} ${cat}`.toLowerCase();
        if (!hay.includes(q)) continue;
      }
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(e);
    }
    return map;
  }, [entries, search, categoryFilter]);

  const categories = useMemo(
    () =>
      Array.from(byCategory.entries())
        .map(([cat, list]) => ({ cat, count: list.length }))
        .sort((a, b) => b.count - a.count || a.cat.localeCompare(b.cat)),
    [byCategory],
  );

  useEffect(() => {
    const w = size.w;
    const h = size.h;
    const cx = w / 2;
    const cy = h / 2;
    const n = categories.length;
    const layoutNodes: LayoutNode[] = [];
    const pad = 56;
    const maxR = Math.min(w, h) / 2 - pad;
    // Leave room around hubs for entry satellites
    const ring = maxR * (n > 8 ? 0.58 : 0.55);

    categories.forEach(({ cat, count }, i) => {
      const angle = n ? (i / n) * Math.PI * 2 - Math.PI / 2 : 0;
      const x = cx + Math.cos(angle) * ring;
      const y = cy + Math.sin(angle) * ring;
      layoutNodes.push({
        id: `cat:${cat}`,
        kind: "category",
        label: cat,
        category: cat,
        count,
        x,
        y,
        homeX: x,
        homeY: y,
        radius: clamp(12 + Math.sqrt(count) * 2.2, 13, 22),
        labelAngle: angle,
      });
    });

    const catPos = new Map(
      layoutNodes.filter((n) => n.kind === "category").map((n) => [n.category, n]),
    );
    const spokes: [string, string][] = [];

    // Always expand all entry satellites around every category hub
    for (const { cat } of categories) {
      const parent = catPos.get(cat);
      const list = byCategory.get(cat) || [];
      if (!parent || !list.length) continue;

      const orbitR = parent.radius + 36 + Math.min(list.length, 8) * 1.5;
      list.forEach((entry, i) => {
        const angle = (i / list.length) * Math.PI * 2 - Math.PI / 2;
        const x = parent.x + Math.cos(angle) * orbitR;
        const y = parent.y + Math.sin(angle) * orbitR;
        const id = `mem:${entry.category}:${entry.key}`;
        layoutNodes.push({
          id,
          kind: "entry",
          label: entry.key,
          category: entry.category || "general",
          valuePreview: valuePreview(entry.value),
          x,
          y,
          homeX: x,
          homeY: y,
          radius: 5.5,
          labelAngle: angle,
        });
        spokes.push([parent.id, id]);
      });
    }

    const prev = new Map(layoutRef.current.nodes.map((n) => [n.id, n]));
    for (const n of layoutNodes) {
      const old = prev.get(n.id);
      if (old) {
        n.x = old.x;
        n.y = old.y;
      }
    }

    layoutRef.current = { nodes: layoutNodes, spokes };
  }, [categories, byCategory, size.w, size.h]);

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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let running = true;

    const tick = () => {
      if (!running) return;
      const { nodes: lns, spokes } = layoutRef.current;
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

      ctx.strokeStyle = "rgba(201, 139, 39, 0.06)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, (Math.min(w, h) / 2 - 70) * 0.72, 0, Math.PI * 2);
      ctx.stroke();

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

      const focusCat =
        sel?.startsWith("cat:") ? sel.slice(4)
        : sel?.startsWith("mem:") ? sel.slice(4).split(":")[0]
        : null;

      // Soft links between adjacent category hubs
      const cats = lns.filter((n) => n.kind === "category");
      for (let i = 0; i < cats.length; i++) {
        const a = cats[i];
        const b = cats[(i + 1) % cats.length];
        if (!a || !b || cats.length < 2) continue;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.quadraticCurveTo(cx, cy, b.x, b.y);
        ctx.strokeStyle = "rgba(201, 139, 39, 0.08)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      for (const [sid, tid] of spokes) {
        const a = nodeMap.get(sid);
        const b = nodeMap.get(tid);
        if (!a || !b) continue;
        const related = !focusCat || a.category === focusCat || b.category === focusCat;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = related
          ? "rgba(160, 185, 220, 0.35)"
          : "rgba(160, 185, 220, 0.08)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      for (const n of lns) {
        if (n.kind !== "category") continue;
        const color = categoryColor(n.category);
        const isSel = n.id === sel || n.category === focusCat;
        const isHov = n.id === hov;
        const dimmed = !!focusCat && !isSel;

        if (isSel || isHov) {
          const glow = ctx.createRadialGradient(n.x, n.y, n.radius * 0.3, n.x, n.y, n.radius * 2.6);
          glow.addColorStop(0, color + "66");
          glow.addColorStop(1, color + "00");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius * 2.6, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? "rgba(18, 35, 61, 0.5)" : "#262626";
        ctx.fill();
        ctx.strokeStyle = dimmed ? color + "44" : isSel ? "#fbe232" : color;
        ctx.lineWidth = isSel ? 2.4 : 1.6;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * 0.32, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? color + "44" : color;
        ctx.fill();

        ctx.font = `600 9px "Segoe UI", system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = dimmed ? "rgba(251, 226, 50, 0.35)" : "#fbe232";
        ctx.fillText(String(n.count || 0), n.x, n.y);

        const angle = n.labelAngle ?? 0;
        const lx = n.x + Math.cos(angle) * (n.radius + 14);
        const ly = n.y + Math.sin(angle) * (n.radius + 14);
        const label = prettyCategory(n.label);
        const short = label.length > 18 ? label.slice(0, 16) + "…" : label;
        ctx.font = `600 ${isSel || isHov ? 11 : 10}px "Segoe UI", system-ui, sans-serif`;
        ctx.fillStyle = dimmed ? "rgba(220, 230, 245, 0.28)" : "#f5f5f5";
        const cos = Math.cos(angle);
        ctx.textAlign = cos > 0.25 ? "left" : cos < -0.25 ? "right" : "center";
        ctx.fillText(short, lx, ly);
      }

      for (const n of lns) {
        if (n.kind !== "entry") continue;
        const color = categoryColor(n.category);
        const isSel = n.id === sel;
        const isHov = n.id === hov;
        const dimmed = !!focusCat && n.category !== focusCat;

        if ((isSel || isHov) && !dimmed) {
          const glow = ctx.createRadialGradient(n.x, n.y, 2, n.x, n.y, 18);
          glow.addColorStop(0, color + "aa");
          glow.addColorStop(1, color + "00");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(n.x, n.y, 18, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, isSel ? 7 : 5.5, 0, Math.PI * 2);
        ctx.fillStyle = dimmed ? color + "44" : color;
        ctx.fill();
        ctx.strokeStyle = isSel ? "#fff" : "rgba(255,255,255,0.35)";
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
        const hitR = n.radius + (n.kind === "category" ? 6 : 5);
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

  const hoverNode = hoverId
    ? layoutRef.current.nodes.find((n) => n.id === hoverId)
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
        onPointerUp={() => {
          dragRef.current = null;
        }}
        onPointerLeave={() => {
          hoverRef.current = null;
          setHoverId(null);
          dragRef.current = null;
        }}
      />

      <div className="absolute left-4 bottom-4 flex flex-wrap gap-3 rounded-xl bg-[#101010]/85 backdrop-blur-md border border-white/10 px-3 py-2 text-[11px] text-white/80">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-[#e8cc12] ring-2 ring-[#e8cc12]/40" />
          Category hub
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-[#3d9b7a]" />
          Memory entry
        </span>
        <span className="text-white/40">· scroll to zoom · drag to pan</span>
      </div>

      {hoverNode && (
        <div className="pointer-events-none absolute right-4 top-4 max-w-sm rounded-xl bg-[#101010]/92 backdrop-blur-md border border-[#fbe232]/25 px-4 py-3 shadow-xl">
          {hoverNode.kind === "category" ? (
            <>
              <div className="text-[10px] uppercase tracking-[0.16em] text-[#fbe232]/90 mb-1">
                Category
              </div>
              <div className="text-sm font-semibold text-white capitalize">
                {prettyCategory(hoverNode.label)}
              </div>
              <div className="text-xs text-white/55 mt-1">
                {hoverNode.count} entries
              </div>
            </>
          ) : (
            <>
              <div className="text-[10px] uppercase tracking-[0.14em] text-white/45 mb-1 capitalize">
                {prettyCategory(hoverNode.category)}
              </div>
              <div className="text-sm font-semibold text-white font-mono">{hoverNode.label}</div>
              <div className="text-xs text-white/70 mt-1.5 line-clamp-3">
                {hoverNode.valuePreview}
              </div>
            </>
          )}
        </div>
      )}

      <div className="absolute right-4 bottom-4 text-[10px] text-white/35 font-mono">
        {Math.round(transform.k * 100)}%
      </div>
    </div>
  );
}
