"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * State that is mirrored in the address bar's query string, so a filtered view can be shared.
 *
 * A change rewrites the query in place with history.replaceState: no navigation, no reload,
 * no new history entry. The first render uses the defaults (the same as the prerendered page);
 * anything in the address bar is applied right after mounting.
 */
export function useUrlState<T extends Record<string, string>>(defaults: T): [T, (patch: Partial<T>) => void, () => void] {
  const [state, setState] = useState<T>(defaults);
  const defaultsRef = useRef(defaults);
  const ready = useRef(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromUrl: Record<string, string> = {};
    for (const key of Object.keys(defaultsRef.current)) {
      const v = params.get(key);
      if (v !== null) fromUrl[key] = v;
    }
    ready.current = true;
    // reading the address bar is only possible after mounting; this is the one sync from it
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (Object.keys(fromUrl).length) setState((s) => ({ ...s, ...fromUrl }));
  }, []);

  useEffect(() => {
    if (!ready.current) return;
    const params = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(state)) {
      if (value === defaultsRef.current[key]) params.delete(key);
      else params.set(key, value);
    }
    const query = params.toString();
    const url = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    if (url !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
      window.history.replaceState(window.history.state, "", url);
    }
  }, [state]);

  const patch = useCallback((p: Partial<T>) => setState((s) => ({ ...s, ...p })), []);
  const reset = useCallback(() => setState(defaultsRef.current), []);
  return [state, patch, reset];
}

export const list = (value: string): string[] => (value ? value.split(",") : []);
export const range = (value: string): [number, number] => value.split("~").map(Number) as [number, number];
