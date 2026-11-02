import { useEffect, useRef } from 'react'
import { animate, createTimeline, stagger } from 'animejs'
import { prefersReducedMotion } from '../lib/motion'

const LEAF =
  'M200 60 C300 80, 340 180, 260 280 C220 330, 150 340, 110 280 C50 190, 90 80, 200 60 Z'

// `at` = when this trace's energy pulse starts (ms), timed to when the main pulse passes its branch point
const traces = [
  { d: 'M200 285 L200 90', w: 8, at: 0, dur: 1400 },        // main vein, grows from the stem upward
  { d: 'M200 240 H220 L245 270', w: 6, at: 320, dur: 600 },
  { d: 'M200 215 H150', w: 6, at: 500, dur: 500 },
  { d: 'M200 190 H275', w: 6, at: 680, dur: 600 },
  { d: 'M200 165 H170 L140 140', w: 6, at: 860, dur: 600 },
  { d: 'M200 140 H228 L255 115', w: 6, at: 1040, dur: 600 },
]

const nodes = [
  { cx: 245, cy: 270, r: 10 },
  { cx: 150, cy: 215, r: 10 },
  { cx: 275, cy: 190, r: 10 },
  { cx: 140, cy: 140, r: 10 },
  { cx: 255, cy: 115, r: 10 },
  { cx: 200, cy: 190, r: 12 }, // central node
]

// Hidden until animated, but only for people who haven't asked for reduced motion.
// pathLength={1} on each path lets us treat every line as "length 1" (see notes below).
const hide =
  'motion-safe:opacity-0 motion-safe:[stroke-dasharray:1] motion-safe:[stroke-dashoffset:1]'

// makes shapes scale around their own centre, not the SVG's top-left corner
const centered = { transformBox: 'fill-box', transformOrigin: 'center' } as const

export function Logo({ size = 48 }: { size?: number }) {
  const floatRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const wrapper = floatRef.current
    const svg = svgRef.current
    if (!wrapper || !svg || prefersReducedMotion()) return

    const outline = svg.querySelector('.leaf-outline')!
    const inner = svg.querySelector('.leaf-inner')!
    const fill = svg.querySelector('.leaf-fill')!
    const traceEls = svg.querySelectorAll('.trace')
    const sparkEls = svg.querySelectorAll('.spark')
    const nodeEls = svg.querySelectorAll('.node')

    const idle: { revert: () => unknown }[] = []

    // runs automatically once the draw-in finishes, so no hard-coded delays
    const startIdle = () => {
      idle.push(
        animate(wrapper, {
          translateY: [0, -10],
          duration: 2600,
          ease: 'inOutSine',
          alternate: true,
          loop: true,
        })
      )

      // energy: one timeline so every pulse stays in sync on each loop
      const energy = createTimeline({ loop: true, loopDelay: 1200, defaults: { ease: 'linear' } })
      sparkEls.forEach((el, i) => {
        energy.add(el, { strokeDashoffset: [0.15, -1], duration: traces[i].dur }, traces[i].at)
      })
      idle.push(energy)

      idle.push(
        animate(nodeEls, {
          scale: [1, 1.25],
          opacity: [1, 0.6],
          duration: 900,
          delay: stagger(200),
          ease: 'inOutSine',
          alternate: true,
          loop: true,
        })
      )
    }

    const draw = createTimeline({ defaults: { ease: 'inOutQuad' }, onComplete: startIdle })
      .add(outline, { strokeDashoffset: [1, 0], opacity: [0, 1], duration: 1600 })
      .add(inner, { strokeDashoffset: [1, 0], opacity: [0, 0.5], duration: 1300 }, '-=1000')
      .add(fill, { opacity: [0, 0.16], duration: 800, ease: 'outQuad' }, '-=500')
      .add(traceEls, { strokeDashoffset: [1, 0], opacity: [0, 1], duration: 700, delay: stagger(130) }, '-=300')
      .add(nodeEls, { scale: [0, 1], opacity: [0, 1], duration: 450, delay: stagger(80), ease: 'outBack' }, '-=400')

    return () => {
      draw.revert()
      idle.forEach((a) => a.revert())
    }
  }, [])

  return (
    <div ref={floatRef} style={{ width: size, height: size }}>
      <svg
        ref={svgRef}
        viewBox="0 0 400 400"
        className="h-full w-full transition-transform duration-300 hover:scale-105"
      >
        <defs>
          <linearGradient id="leafStroke" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="100%" stopColor="#059669" />
          </linearGradient>

          {/* soft neon glow. userSpaceOnUse matters: see notes */}
          <filter id="energyGlow" filterUnits="userSpaceOnUse" x="0" y="0" width="400" height="400">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* faint fill */}
        <path className="leaf-fill opacity-[0.16] motion-safe:opacity-0" d={LEAF} fill="url(#leafStroke)" />

        {/* wireframe: outer outline + smaller inner outline */}
        <path
          className={`leaf-outline ${hide}`}
          d={LEAF}
          pathLength={1}
          fill="none"
          stroke="url(#leafStroke)"
          strokeWidth="5"
          strokeLinejoin="round"
        />
        <path
          className={`leaf-inner opacity-50 ${hide}`}
          d={LEAF}
          pathLength={1}
          transform="translate(36 36) scale(0.82)"
          fill="none"
          stroke="url(#leafStroke)"
          strokeWidth="3"
          strokeLinejoin="round"
        />

        {/* circuits + energy + nodes, all glowing */}
        <g filter="url(#energyGlow)">
          {traces.map((t) => (
            <path
              key={t.d}
              className={`trace ${hide}`}
              d={t.d}
              pathLength={1}
              fill="none"
              stroke="#34D399"
              strokeWidth={t.w}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}

          {/* the energy pulses: a short bright dash that travels along a copy of each trace */}
          <g className="motion-reduce:hidden">
            {traces.map((t) => (
              <path
                key={t.d}
                className="spark [stroke-dashoffset:0.15]"
                d={t.d}
                pathLength={1}
                fill="none"
                stroke="#ECFDF5"
                strokeWidth={t.w - 2}
                strokeDasharray="0.15 1"
              />
            ))}
          </g>

          {nodes.map((n) => (
            <circle
              key={`${n.cx}-${n.cy}`}
              className="node motion-safe:opacity-0"
              style={centered}
              cx={n.cx}
              cy={n.cy}
              r={n.r}
              fill="#A7F3D0"
            />
          ))}
        </g>
      </svg>
    </div>
  )
}