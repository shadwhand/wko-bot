import { useRef, useEffect, useState, useCallback } from 'react'
import styles from './ChartContainer.module.css'

interface ChartContainerProps {
  /** Render function called when container resizes. Receives SVG element, width, height. */
  renderChart: (svg: SVGSVGElement, width: number, height: number) => void | (() => void)
  /** Minimum height in pixels. Default 200. */
  minHeight?: number
  /** Aspect ratio (width/height). If set, height is computed from width. */
  aspectRatio?: number
  className?: string
}

export function ChartContainer({
  renderChart,
  minHeight = 200,
  aspectRatio,
  className,
}: ChartContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null)

  const measure = useCallback(() => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const width = Math.floor(rect.width)
    const height = aspectRatio
      ? Math.max(Math.floor(width / aspectRatio), minHeight)
      : Math.max(Math.floor(rect.height), minHeight)
    setDimensions((prev) => {
      if (prev?.width === width && prev?.height === height) return prev
      return { width, height }
    })
  }, [aspectRatio, minHeight])

  // ResizeObserver for responsive charts
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const observer = new ResizeObserver(() => {
      measure()
    })
    observer.observe(el)
    measure() // Initial measurement

    return () => observer.disconnect()
  }, [measure])

  // Render chart when dimensions change
  useEffect(() => {
    if (!dimensions || !svgRef.current) return
    const cleanup = renderChart(svgRef.current, dimensions.width, dimensions.height)
    return () => {
      if (typeof cleanup === 'function') cleanup()
    }
  }, [dimensions, renderChart])

  return (
    <div
      ref={containerRef}
      className={`${styles.container} ${className ?? ''}`}
      style={{ minHeight }}
    >
      {dimensions && (
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className={styles.svg}
        />
      )}
    </div>
  )
}
