"use client";

/*
 * Liquid glass surface and button.
 *
 * Adapted from the Sera UI "Liquid Glass" component (https://seraui.com/docs/liquid-glass),
 * MIT License, Copyright (c) 2025 Sera UI. The SVG filter (a displacement map with a separate
 * offset per colour channel, which bends and slightly splits the light of whatever is behind
 * the surface) and the presets are Sera UI's. Changes made here:
 *   - `Glass` is exported, so it can wrap panels as well as buttons;
 *   - a `layout` prop: "center" is the original button layout, "block" leaves the content alone;
 *   - a `panel` preset with a gentler bend for large surfaces that hold text;
 *   - this app is dark only, so the dark styling is always used (no flash of the light style);
 *   - the class helper is this project's `cn`.
 *
 * Browsers that cannot use an SVG filter as a backdrop (Safari, Firefox) get a blurred backdrop.
 */

import { cva } from "class-variance-authority";
import React, { useEffect, useId, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/utils";

const GLASS_PRESETS = {
  subtle: {
    backgroundOpacity: 0.06,
    saturation: 1.1,
    brightness: 55,
    blur: 8,
    displace: 0.3,
    distortionScale: -80,
    redOffset: -2,
    greenOffset: 6,
    blueOffset: 12,
    mixBlendMode: "difference",
  },
  default: {
    backgroundOpacity: 0.1,
    saturation: 1.4,
    brightness: 55,
    blur: 10,
    displace: 0.5,
    distortionScale: -160,
    redOffset: 0,
    greenOffset: 8,
    blueOffset: 16,
    mixBlendMode: "difference",
  },
  bold: {
    backgroundOpacity: 0.18,
    saturation: 1.8,
    brightness: 60,
    blur: 12,
    displace: 0.8,
    distortionScale: -240,
    redOffset: 6,
    greenOffset: 12,
    blueOffset: 24,
    mixBlendMode: "screen",
  },
  ghost: {
    backgroundOpacity: 0,
    saturation: 1,
    brightness: 55,
    blur: 6,
    displace: 0,
    distortionScale: 0,
    redOffset: 0,
    greenOffset: 0,
    blueOffset: 0,
    mixBlendMode: "difference",
  },
  // Large surfaces that hold numbers and text: a darker body and a gentler bend at the rim.
  panel: {
    backgroundOpacity: 0.34,
    saturation: 1.3,
    brightness: 55,
    blur: 10,
    displace: 0.4,
    distortionScale: -110,
    redOffset: 0,
    greenOffset: 5,
    blueOffset: 10,
    mixBlendMode: "difference",
  },
};

export type GlassVariant = keyof typeof GLASS_PRESETS;

const GLASS_DEFAULTS = {
  width: "auto" as number | string,
  height: "auto" as number | string,
  borderRadius: 20,
  borderWidth: 0.07,
  opacity: 0.93,
  xChannel: "R" as "R" | "G" | "B" | "A",
  yChannel: "G" as "R" | "G" | "B" | "A",
};

export interface GlassProps {
  variant?: GlassVariant;
  /** "center" (the button layout) or "block" (content laid out by the caller). */
  layout?: "center" | "block";
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  width?: number | string;
  height?: number | string;
  borderRadius?: number;
  borderWidth?: number;
  brightness?: number;
  opacity?: number;
  blur?: number;
  displace?: number;
  backgroundOpacity?: number;
  saturation?: number;
  distortionScale?: number;
  redOffset?: number;
  greenOffset?: number;
  blueOffset?: number;
  xChannel?: "R" | "G" | "B" | "A";
  yChannel?: "R" | "G" | "B" | "A";
  mixBlendMode?: string;
}

const EMPTY_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1' height='1'%3E%3C/svg%3E";

export function Glass(rawProps: GlassProps) {
  const {
    variant = "default",
    layout = "center",
    children,
    className = "",
    style = {},
    width,
    height,
    borderRadius,
    borderWidth,
    brightness,
    opacity,
    blur,
    displace,
    backgroundOpacity,
    saturation,
    distortionScale,
    redOffset,
    greenOffset,
    blueOffset,
    xChannel,
    yChannel,
    mixBlendMode,
  } = rawProps;

  const uniqueId = useId().replace(/:/g, "-");
  const filterId = `glass-filter-${uniqueId}`;
  const redGradId = `red-grad-${uniqueId}`;
  const blueGradId = `blue-grad-${uniqueId}`;

  const containerRef = useRef<HTMLDivElement>(null);
  const feImageRef = useRef<SVGFEImageElement>(null);
  const redChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const greenChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const blueChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const gaussianBlurRef = useRef<SVGFEGaussianBlurElement>(null);

  const v = useMemo(() => {
    const p = GLASS_PRESETS[variant] ?? GLASS_PRESETS.default;
    return {
      ...GLASS_DEFAULTS,
      ...p,
      ...(width !== undefined && { width }),
      ...(height !== undefined && { height }),
      ...(borderRadius !== undefined && { borderRadius }),
      ...(borderWidth !== undefined && { borderWidth }),
      ...(brightness !== undefined && { brightness }),
      ...(opacity !== undefined && { opacity }),
      ...(blur !== undefined && { blur }),
      ...(displace !== undefined && { displace }),
      ...(backgroundOpacity !== undefined && { backgroundOpacity }),
      ...(saturation !== undefined && { saturation }),
      ...(distortionScale !== undefined && { distortionScale }),
      ...(redOffset !== undefined && { redOffset }),
      ...(greenOffset !== undefined && { greenOffset }),
      ...(blueOffset !== undefined && { blueOffset }),
      ...(xChannel !== undefined && { xChannel }),
      ...(yChannel !== undefined && { yChannel }),
      ...(mixBlendMode !== undefined && { mixBlendMode }),
    };
  }, [variant, width, height, borderRadius, borderWidth, brightness, opacity, blur, displace, backgroundOpacity, saturation, distortionScale, redOffset, greenOffset, blueOffset, xChannel, yChannel, mixBlendMode]);

  /** The displacement map for the surface at its current size, as a data URL. */
  const displacementMap = (actualWidth: number, actualHeight: number) => {
    const edgeSize = Math.min(actualWidth, actualHeight) * (v.borderWidth * 0.5);
    const svgContent = `
      <svg viewBox="0 0 ${actualWidth} ${actualHeight}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="${redGradId}" x1="100%" y1="0%" x2="0%" y2="0%">
            <stop offset="0%" stop-color="#0000"/>
            <stop offset="100%" stop-color="red"/>
          </linearGradient>
          <linearGradient id="${blueGradId}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0000"/>
            <stop offset="100%" stop-color="blue"/>
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" fill="black"></rect>
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${v.borderRadius}" fill="url(#${redGradId})" />
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${v.borderRadius}" fill="url(#${blueGradId})" style="mix-blend-mode: ${v.mixBlendMode}" />
        <rect x="${edgeSize}" y="${edgeSize}" width="${actualWidth - edgeSize * 2}" height="${actualHeight - edgeSize * 2}" rx="${v.borderRadius}" fill="hsl(0 0% ${v.brightness}% / ${v.opacity})" style="filter:blur(${v.blur}px)" />
      </svg>
    `;
    return `data:image/svg+xml,${encodeURIComponent(svgContent)}`;
  };

  const updateDisplacementMap = () => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (feImageRef.current && rect && rect.width > 0 && rect.height > 0) {
      feImageRef.current.setAttribute("href", displacementMap(rect.width, rect.height));
    }
  };

  useEffect(() => {
    updateDisplacementMap();
    [
      { ref: redChannelRef, offset: v.redOffset },
      { ref: greenChannelRef, offset: v.greenOffset },
      { ref: blueChannelRef, offset: v.blueOffset },
    ].forEach(({ ref, offset }) => {
      if (ref.current) {
        ref.current.setAttribute("scale", (v.distortionScale + offset).toString());
        ref.current.setAttribute("xChannelSelector", v.xChannel);
        ref.current.setAttribute("yChannelSelector", v.yChannel);
      }
    });
    if (gaussianBlurRef.current) {
      gaussianBlurRef.current.setAttribute("stdDeviation", v.displace.toString());
    }
    // the map is rebuilt whenever any setting that shapes it changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [v]);

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver(() => {
      setTimeout(updateDisplacementMap, 0);
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
    // the observer is set up once; it reads the latest settings through the refs
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // What the browser can do is only known after mounting; both start true so that the
  // prerendered markup and the first client render agree.
  const [svgFilterSupported, setSvgFilterSupported] = useState(true);
  const [backdropFilterSupported, setBackdropFilterSupported] = useState(true);

  useEffect(() => {
    const isWebkit = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
    const isFirefox = /Firefox/.test(navigator.userAgent);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSvgFilterSupported(!isWebkit && !isFirefox);
    setBackdropFilterSupported(CSS.supports("backdrop-filter", "blur(10px)"));
  }, []);

  // The distortion is recomputed for every frame in which anything behind the surface changes.
  // While the page scrolls, that is every frame, and scrolling stutters. So the distortion is
  // switched off for as long as the page is moving and comes back when it stops; the rim light,
  // the sheen and the tint stay throughout. The style is set on the element directly, so React
  // does not render again on every scroll event.
  useEffect(() => {
    const el = containerRef.current;
    if (!el || !svgFilterSupported) return;
    const full = `url(#${filterId}) saturate(${v.saturation})`;
    let timer: number | undefined;
    const settle = () => {
      el.style.backdropFilter = full;
      timer = undefined;
    };
    const onScroll = () => {
      if (timer === undefined) el.style.backdropFilter = "none";
      else window.clearTimeout(timer);
      timer = window.setTimeout(settle, 180);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (timer !== undefined) window.clearTimeout(timer);
      el.style.backdropFilter = full;
    };
  }, [filterId, svgFilterSupported, v.saturation]);

  const containerStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      ...style,
      width: typeof v.width === "number" ? `${v.width}px` : v.width,
      height: typeof v.height === "number" ? `${v.height}px` : v.height,
      borderRadius: `${v.borderRadius}px`,
    };
    if (svgFilterSupported) {
      return {
        ...base,
        background: `hsl(0 0% 0% / ${v.backgroundOpacity})`,
        backdropFilter: `url(#${filterId}) saturate(${v.saturation})`,
        boxShadow: `0 0 2px 1px color-mix(in oklch, white, transparent 65%) inset,
                    0 0 10px 4px color-mix(in oklch, white, transparent 85%) inset,
                    0px 4px 16px rgba(17, 17, 26, 0.05),
                    0px 8px 24px rgba(17, 17, 26, 0.05),
                    0px 16px 56px rgba(17, 17, 26, 0.05),
                    0px 4px 16px rgba(17, 17, 26, 0.05) inset,
                    0px 8px 24px rgba(17, 17, 26, 0.05) inset,
                    0px 16px 56px rgba(17, 17, 26, 0.05) inset`,
      };
    }
    if (!backdropFilterSupported) {
      return {
        ...base,
        background: "rgba(0, 0, 0, 0.4)",
        border: "1px solid rgba(255, 255, 255, 0.2)",
        boxShadow: "inset 0 1px 0 0 rgba(255, 255, 255, 0.2), inset 0 -1px 0 0 rgba(255, 255, 255, 0.1)",
      };
    }
    return {
      ...base,
      background: `rgba(255, 255, 255, ${Math.max(0.04, 0.1 - v.backgroundOpacity * 0.15)})`,
      backdropFilter: "blur(12px) saturate(1.8) brightness(1.2)",
      WebkitBackdropFilter: "blur(12px) saturate(1.8) brightness(1.2)",
      border: "1px solid rgba(255, 255, 255, 0.2)",
      boxShadow: "inset 0 1px 0 0 rgba(255, 255, 255, 0.2), inset 0 -1px 0 0 rgba(255, 255, 255, 0.1)",
    };
  };

  return (
    <div
      ref={containerRef}
      data-slot="liquid-glass"
      className={cn(
        "relative overflow-hidden transition-opacity duration-[260ms] ease-out",
        layout === "center" && "flex items-center justify-center",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber",
        className,
      )}
      style={containerStyles()}
    >
      <svg aria-hidden className="pointer-events-none absolute inset-0 -z-10 h-full w-full opacity-0" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id={filterId} colorInterpolationFilters="sRGB" x="0%" y="0%" width="100%" height="100%">
            <feImage ref={feImageRef} href={EMPTY_IMAGE} x="0" y="0" width="100%" height="100%" preserveAspectRatio="none" result="map" />

            <feDisplacementMap ref={redChannelRef} in="SourceGraphic" in2="map" result="dispRed" />
            <feColorMatrix in="dispRed" type="matrix" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="red" />

            <feDisplacementMap ref={greenChannelRef} in="SourceGraphic" in2="map" result="dispGreen" />
            <feColorMatrix in="dispGreen" type="matrix" values="0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0" result="green" />

            <feDisplacementMap ref={blueChannelRef} in="SourceGraphic" in2="map" result="dispBlue" />
            <feColorMatrix in="dispBlue" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0" result="blue" />

            <feBlend in="red" in2="green" mode="screen" result="rg" />
            <feBlend in="rg" in2="blue" mode="screen" result="output" />
            <feGaussianBlur ref={gaussianBlurRef} in="output" stdDeviation="0.7" />
          </filter>
        </defs>
      </svg>

      <div className={cn("relative z-10 h-full w-full rounded-[inherit]", layout === "center" && "flex items-center justify-center p-2")}>{children}</div>
    </div>
  );
}

const glassButtonSizes = cva("rounded-[inherit]", {
  variants: {
    size: {
      sm: "px-2.5 py-0.5 text-[0.8rem]",
      md: "px-4 py-2",
      lg: "px-6 py-3 text-lg",
      icon: "size-10 p-2",
    },
  },
  defaultVariants: { size: "md" },
});

export type GlassButtonProps = {
  children: React.ReactNode;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  className?: string;
  variant?: GlassVariant;
  size?: "sm" | "md" | "lg" | "icon";
  textClassName?: string;
  disabled?: boolean;
  type?: "button" | "submit";
  title?: string;
} & Omit<GlassProps, "children" | "variant" | "className" | "style" | "layout">;

export function GlassButton({
  children,
  onClick,
  className = "",
  variant = "default",
  size = "md",
  textClassName = "inline-flex items-center gap-1.5 font-medium text-foreground [&_svg]:size-3.5",
  disabled,
  type = "button",
  title,
  ...surfaceOverrides
}: GlassButtonProps) {
  return (
    <button
      type={type}
      title={title}
      onClick={onClick}
      disabled={disabled}
      data-slot="glass-button"
      className={cn(
        "relative inline-flex cursor-pointer items-center justify-center select-none",
        "transform transition-transform duration-150 ease-in-out active:scale-95",
        "rounded-[14px] focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber disabled:pointer-events-none disabled:opacity-50",
        className,
      )}
    >
      <Glass variant={variant} borderRadius={14} className={cn(glassButtonSizes({ size }))} {...surfaceOverrides}>
        <span className={cn(textClassName)}>{children}</span>
      </Glass>
    </button>
  );
}

export default GlassButton;
