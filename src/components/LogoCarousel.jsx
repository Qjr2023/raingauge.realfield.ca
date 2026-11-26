import { useEffect, useState } from 'react';
import { PARTNER_LOGOS } from '../config/logos';

const ROTATE_MS = 4000;

/**
 * Cycles through partner/sponsor logos in the footer, one at a time,
 * with a soft crossfade. Pauses on hover/focus so it doesn't move under
 * a pointer or keyboard user, and skips the crossfade under
 * prefers-reduced-motion (handled in CSS).
 */
function LogoCarousel() {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused || PARTNER_LOGOS.length <= 1) return undefined;
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % PARTNER_LOGOS.length);
    }, ROTATE_MS);
    return () => clearInterval(timer);
  }, [paused]);

  return (
    <div
      className="logo-carousel"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      {PARTNER_LOGOS.map((logo, i) => (
        <img
          key={logo.src}
          src={logo.src}
          alt={i === index ? logo.alt : ''}
          aria-hidden={i === index ? undefined : true}
          className={
            i === index ? 'logo-carousel-img is-active' : 'logo-carousel-img'
          }
        />
      ))}
    </div>
  );
}

export default LogoCarousel;
