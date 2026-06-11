import { useEffect, useState } from "react";
import { api } from "@/services/api";

/**
 * Renders an image from a JWT-protected endpoint. Plain <img src> can't send
 * the Authorization header, so we fetch the bytes via axios and hand the
 * <img> a blob object URL instead.
 */
export function AuthImage({
  path,
  alt,
  className,
}: {
  path: string;
  alt: string;
  className?: string;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let url: string | null = null;
    let active = true;
    setFailed(false);
    setSrc(null);
    api
      .get(path, { responseType: "blob" })
      .then((res) => {
        if (!active) return;
        url = URL.createObjectURL(res.data);
        setSrc(url);
      })
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [path]);

  if (failed)
    return (
      <div className="flex h-40 items-center justify-center rounded-md bg-slate-100 text-xs text-slate-400">
        image unavailable
      </div>
    );
  if (!src)
    return (
      <div className="h-40 animate-pulse rounded-md bg-slate-100" aria-hidden />
    );
  return <img src={src} alt={alt} className={className} />;
}
