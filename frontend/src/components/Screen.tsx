import { useNavigate } from "@tanstack/react-router";
import type { MouseEvent } from "react";

export function Screen({ html }: { html: string }) {
  const navigate = useNavigate();
  const onClick = (e: MouseEvent<HTMLDivElement>) => {
    const a = (e.target as HTMLElement).closest("a");
    const href = a?.getAttribute("href");
    if (!href) return;
    e.preventDefault();
    if (href.startsWith("/")) navigate({ to: href });
  };
  return <div onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />;
}
