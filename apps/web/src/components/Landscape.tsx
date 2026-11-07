import { useLocale } from "./shared";
export default function Landscape() {
  const bn = useLocale() === "bn";
  return (
    <svg
      className="hero-landscape"
      viewBox="0 0 620 490"
      role="img"
      aria-label={
        bn
          ? "নদী, মাঠ, বাড়ি আর গাছের আঁকা ভূদৃশ্য।"
          : "An illustrated landscape with a river, fields, houses, and trees."
      }
    >
      <defs>
        <pattern
          id="field"
          width="26"
          height="26"
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(-13)"
        >
          <path
            d="M0 4h26M0 17h26"
            stroke="#8ca36a"
            strokeWidth="1.2"
            opacity=".5"
          />
        </pattern>
        <pattern id="paper" width="6" height="6" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="3" r=".45" fill="#726d4e" opacity=".1" />
        </pattern>
      </defs>
      <rect x="22" y="18" width="575" height="449" rx="20" fill="#e8e5cd" />
      <rect x="22" y="18" width="575" height="449" rx="20" fill="url(#paper)" />
      <path d="M24 20h360l-22 112-115 67-222-45Z" fill="#cfdaa8" />
      <path d="M26 322 210 285l95 180H26Z" fill="#b8cb94" />
      <path d="m308 310 287-145v299H361Z" fill="#d7dbb0" />
      <path d="m65 351 143-30 76 145H33Z" fill="url(#field)" />
      <path d="m454 308 130-65v147l-104 30Z" fill="url(#field)" />
      <path
        d="M608 49C440 81 452 175 321 188S250 262 152 272 53 282 3 328"
        stroke="#e7eedc"
        strokeWidth="95"
        fill="none"
      />
      <path
        d="M608 49C440 81 452 175 321 188S250 262 152 272 53 282 3 328"
        stroke="#81b6bd"
        strokeWidth="71"
        fill="none"
      />
      <path
        d="M608 44C440 79 449 172 321 185S252 258 152 269 50 284 5 323"
        stroke="#a8cbd0"
        strokeWidth="9"
        fill="none"
        opacity=".6"
      />
      <path
        d="M140 17 165 145 285 156M598 356 378 376 272 294 284 230M27 97l171 15"
        stroke="#faf7e6"
        strokeWidth="9"
        fill="none"
      />
      <path
        d="M140 17 165 145 285 156M598 356 378 376 272 294 284 230"
        stroke="#c5c4ad"
        strokeWidth="1"
        strokeDasharray="4 5"
        fill="none"
      />
      <g fill="#547653">
        <circle cx="75" cy="158" r="22" />
        <circle cx="113" cy="163" r="17" />
        <circle cx="64" cy="131" r="15" />
        <circle cx="364" cy="57" r="29" />
        <circle cx="395" cy="48" r="20" />
        <circle cx="559" cy="290" r="21" />
        <circle cx="530" cy="282" r="14" />
        <circle cx="445" cy="437" r="27" />
      </g>
      <g fill="#6c8e5e">
        <circle cx="66" cy="149" r="15" />
        <circle cx="365" cy="44" r="22" />
        <circle cx="554" cy="283" r="16" />
        <circle cx="445" cy="426" r="18" />
      </g>
      <g>
        <path d="m206 52 43-23 42 23v35h-85Z" fill="#f6edd8" />
        <path d="m200 54 49-29 48 29-8 6-40-24-40 24Z" fill="#b56f4c" />
        <rect x="245" y="62" width="13" height="25" rx="1" fill="#598280" />
        <rect x="218" y="64" width="15" height="12" fill="#94b6ad" />
        <path d="m350 277 30-18 34 18v28h-64Z" fill="#faf0d9" />
        <path d="m346 278 34-23 38 23-5 7-33-21-29 21Z" fill="#ad7051" />
        <rect x="373" y="285" width="11" height="20" fill="#547573" />
        <path d="m473 168 27-16 28 16v24h-55Z" fill="#f5e9d3" />
        <path d="m467 169 33-22 34 22-5 5-29-18-27 18Z" fill="#b17d5a" />
      </g>
      <g transform="translate(201 222) rotate(-11)">
        <path d="M0 0c17 13 34 13 53 0-4 20-42 20-53 0Z" fill="#536c65" />
        <path d="M25-28v33" stroke="#f7efdd" strokeWidth="2" />
        <path d="M26-27 46-1H26Z" fill="#f4e6bd" />
      </g>
      <g transform="translate(482 55)">
        <circle cx="35" cy="30" r="28" fill="#f3cf78" opacity=".9" />
        <path
          d="M35 0v-8M35 60v8M5 30h-8M65 30h8M14 9 9 4M56 51l5 5"
          stroke="#c39947"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </g>
      <g transform="translate(63 385) rotate(-12)">
        <rect width="160" height="43" rx="5" fill="#faf8ed" />
        <path d="M14 21c6-13 14-13 20 0-6 11-15 11-20 0" fill="#598069" />
        <text
          x="43"
          y="27"
          fontSize="14"
          fontFamily="Noto Sans Bengali,DM Sans,sans-serif"
          fontWeight="600"
          fill="#385b4c"
        >
          {bn ? "গল্পের শুরু।" : "A place to begin."}
        </text>
      </g>
      <g transform="translate(539 403)">
        <circle r="24" fill="#f8f4e8" />
        <path d="M0-17 5 0H-5Z" fill="#496c5a" />
        <path d="M0 17 5 0H-5Z" fill="#a3b59b" />
        <text
          x="-4"
          y="-29"
          fontSize="11"
          fill="#496c5a"
          fontFamily="sans-serif"
        >
          N
        </text>
      </g>
    </svg>
  );
}
