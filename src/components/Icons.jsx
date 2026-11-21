function Svg({ size = 20, children, ...rest }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {children}
    </svg>
  );
}

export function DropIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M12 2.5c-3.6 4.6-6.5 8.3-6.5 11.6a6.5 6.5 0 0 0 13 0c0-3.3-2.9-7-6.5-11.6z"
        fill="currentColor"
      />
      <path
        d="M9 14.5a3 3 0 0 0 3 3"
        stroke="#fff"
        strokeWidth="1.6"
        fill="none"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function LayersIcon(props) {
  return (
    <Svg {...props}>
      <path d="M12 3 2.5 8 12 13l9.5-5z" />
      <path d="m2.5 12.5 9.5 5 9.5-5" />
      <path d="m2.5 16.5 9.5 5 9.5-5" opacity="0.6" />
    </Svg>
  );
}

export function InfoIcon(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6" />
      <path d="M12 7.5h.01" />
    </Svg>
  );
}

export function ChartIcon(props) {
  return (
    <Svg strokeWidth="2.2" {...props}>
      <path d="M4 20h16" />
      <path d="M7 16v-4" />
      <path d="M12 16V7" />
      <path d="M17 16v-7" />
    </Svg>
  );
}

export function TapIcon(props) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="10" r="3" />
      <path d="M12 2v2M12 16v6M4 10H2M22 10h-2M6.3 4.3l1.4 1.4M16.3 4.3l-1.4 1.4" />
    </Svg>
  );
}

export function CheckIcon(props) {
  return (
    <Svg strokeWidth="2.6" {...props}>
      <path d="m5 12.5 4.5 4.5L19 7.5" />
    </Svg>
  );
}

export function CloseIcon(props) {
  return (
    <Svg strokeWidth="2.4" {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </Svg>
  );
}

export function InstallIcon(props) {
  return (
    <Svg {...props}>
      <rect x="6" y="2.5" width="12" height="19" rx="2" />
      <path d="M12 7v7" />
      <path d="m9 11.5 3 3 3-3" />
      <path d="M10.5 18.5h3" />
    </Svg>
  );
}
