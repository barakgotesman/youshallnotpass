/** Visual state of the lantern glow behind the wizard. */
export type GlowState = 'idle' | 'thinking' | 'open'

/** Props for {@link Backdrop}. */
type BackdropProps = {
  /** `thinking` while the guard replies, `open` once the gate is opened. */
  glow: GlowState
}

/**
 * Full-screen illustration behind the game, with the lantern glow on top.
 *
 * Purely decorative, so it is hidden from assistive tech. On wide screens the
 * wizard (bottom-left) stays visible beside the centered chat; on phones the
 * image shifts to the fiery tower because the chat covers the wizard anyway.
 *
 * @param props - See {@link BackdropProps}.
 * @returns The background layer.
 */
export function Backdrop({ glow }: BackdropProps) {
  return (
    <div aria-hidden="true" className="absolute inset-0 overflow-hidden">
      <img
        src="/bg-wizard.webp"
        alt=""
        className="h-full w-full object-cover object-[85%_0%] md:object-left-bottom"
      />
      {/* The glow is positioned for the bottom-left crop, so it only exists where that crop does. */}
      <div className="lantern-glow hidden md:block" data-state={glow} />
    </div>
  )
}
