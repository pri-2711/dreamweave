import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/content.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/content")({
  head: () => ({
    meta: [
      { title: "Japan Trip Content Vault — DreamWeave" },
      { name: "description", content: "All saved photos, notes, tickets and links for the Japan Trip." },
      { property: "og:title", content: "Japan Trip Content Vault — DreamWeave" },
      { property: "og:description", content: "All saved photos, notes, tickets and links for the Japan Trip." },
    ],
  }),
  component: () => <Screen html={html} />,
});
