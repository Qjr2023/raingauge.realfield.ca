import { useEffect, useState } from 'react';

const LOGOS = [
  {
    src: `${import.meta.env.BASE_URL}logos/agbio.png`,
    alt: 'College of Agriculture and Bioresources',
  },
  {
    src: `${import.meta.env.BASE_URL}logos/aci.png`,
    alt: 'Agronomic Crop Imaging Lab',
  },
  {
    src: `${import.meta.env.BASE_URL}logos/ndac.png`,
    alt: 'Nutrien Digital Agriculture Centre',
  },
  {
    src: `${import.meta.env.BASE_URL}logos/acreage.png`,
    alt: 'ACREAGE Digital Agriculture — Agroecosystem Digital Twins and Intelligent Systems',
  },
  {
    src: `${import.meta.env.BASE_URL}logos/realfield.png`,
    alt: 'RealField',
  },
];

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
    if (paused || LOGOS.length <= 1) return undefined;
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % LOGOS.length);
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
      {LOGOS.map((logo, i) => (
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
