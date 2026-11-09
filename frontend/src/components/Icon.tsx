// A handful of simple line icons, drawn inline so there's no icon library to install.
// They inherit the text color (currentColor) and are hidden from screen readers;
// the button or link next to them always carries the words.

const PATHS = {
  logo: 'M12 3c-4 3.5-6 7-6 10a6 6 0 0 0 12 0c0-3-2-6.5-6-10Z M12 21v-7 M12 16l-2.5-2.5 M12 14l2.5-2.5',
  today:
    'M12 4V2 M12 22v-2 M4 12H2 M22 12h-2 M5.6 5.6 4.2 4.2 M19.8 19.8l-1.4-1.4 M5.6 18.4l-1.4 1.4 M19.8 4.2l-1.4 1.4 M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
  trends: 'M3 3v18h18 M7 15l4-4 3 3 5-6',
  settings:
    'M4 6h3 M11 6h9 M4 12h9 M17 12h3 M4 18h5 M13 18h7 M11 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z M17 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z M13 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z',
  left: 'M15 18l-6-6 6-6',
  right: 'M9 18l6-6-6-6',
  plus: 'M12 5v14 M5 12h14',
  minus: 'M5 12h14',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  moon: 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z',
  note: 'M5 4h10l4 4v12H5Z M15 4v4h4 M8 12h8 M8 16h5',
  pulse: 'M3 12h4l2-5 4 10 2-5h6',
  spark: 'M12 3v4 M12 17v4 M3 12h4 M17 12h4 M6 6l2.5 2.5 M15.5 15.5 18 18 M6 18l2.5-2.5 M15.5 8.5 18 6',
  close: 'M6 6l12 12 M18 6 6 18',
  cycle: 'M12 3a9 9 0 1 1-9 9 M12 3v4 M12 3H8 M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
  drop: 'M12 3c-3.5 4.5-6 7.8-6 11a6 6 0 0 0 12 0c0-3.2-2.5-6.5-6-11Z',
  edit: 'M4 20h4L19 9l-4-4L4 16Z M13.5 6.5l4 4',
  trash: 'M4 7h16 M9 7V4h6v3 M6 7l1 13h10l1-13 M10 11v6 M14 11v6',
  calendar: 'M4 6h16v14H4Z M4 10h16 M8 3v4 M16 3v4',
  pill: 'M10.5 20.5a5 5 0 0 1-7-7l6-6a5 5 0 0 1 7 7Z M8.5 8.5l7 7',
  stop: 'M6 6h12v12H6Z',
  skip: 'M6 6l12 12',
  bowl: 'M3 11h18a9 9 0 0 1-18 0Z M7 8c0-2 2-2 2-4 M12 8c0-2 2-2 2-4',
  flask: 'M9 3h6 M10 3v6l-5.2 9.2A2 2 0 0 0 6.5 21h11a2 2 0 0 0 1.7-2.8L14 9V3 M7.3 15h9.4',
} as const

export type IconName = keyof typeof PATHS

export default function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.9}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  )
}
