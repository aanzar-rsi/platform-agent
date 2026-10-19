"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

interface SwapCardProps {
  children: React.ReactNode
  className?: string
  duration?: number
}

interface SwapCardItemProps {
  children: React.ReactNode
  isActive: boolean
  index: number
  className?: string
}

const SwapCardContext = React.createContext<{
  activeIndex: number
  setActiveIndex: (index: number) => void
  totalItems: number
}>({
  activeIndex: 0,
  setActiveIndex: () => {},
  totalItems: 0,
})

export function SwapCard({ children, className, duration = 4000 }: SwapCardProps) {
  const [activeIndex, setActiveIndex] = React.useState(0)
  const items = React.Children.toArray(children)
  const totalItems = items.length

  // Auto-rotate
  React.useEffect(() => {
    if (totalItems <= 1) return
    
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % totalItems)
    }, duration)

    return () => clearInterval(interval)
  }, [totalItems, duration])

  return (
    <SwapCardContext.Provider value={{ activeIndex, setActiveIndex, totalItems }}>
      <div className={cn("relative w-full h-full", className)}>
        {children}
      </div>
    </SwapCardContext.Provider>
  )
}

export function SwapCardItem({ children, isActive: _isActive, index, className }: SwapCardItemProps) {
  const { activeIndex } = React.useContext(SwapCardContext)
  const isActive = activeIndex === index
  
  return (
    <AnimatePresence mode="wait">
      {isActive && (
        <motion.div
          key={index}
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{
            duration: 0.5,
            ease: [0.4, 0, 0.2, 1],
          }}
          className={cn("absolute inset-0", className)}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function SwapCardIndicators({ className }: { className?: string }) {
  const { activeIndex, setActiveIndex, totalItems } = React.useContext(SwapCardContext)

  return (
    <div className={cn("flex gap-2 justify-center", className)}>
      {Array.from({ length: totalItems }).map((_, index) => (
        <button
          key={index}
          onClick={() => setActiveIndex(index)}
          className={cn(
            "h-2 rounded-full transition-all duration-300",
            activeIndex === index
              ? "w-8 bg-[#171717]"
              : "w-2 bg-[#171717]/30 hover:bg-[#171717]/50"
          )}
          aria-label={`Go to slide ${index + 1}`}
        />
      ))}
    </div>
  )
}

// Helper hook to use swap card context
export function useSwapCard() {
  const context = React.useContext(SwapCardContext)
  if (!context) {
    throw new Error("useSwapCard must be used within SwapCard")
  }
  return context
}
