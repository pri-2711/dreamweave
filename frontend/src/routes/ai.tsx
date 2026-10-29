import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/ai.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/ai")({
  head: () => ({
    meta: [
      { title: "Dream AI — DreamWeave" },
      { name: "description", content: "Dream AI co-creator that turns your saved pins into itineraries and ideas." },
      { property: "og:title", content: "Dream AI — DreamWeave" },
      { property: "og:description", content: "Dream AI co-creator that turns your saved pins into itineraries and ideas." },
    ],
  }),
  component: () => <Screen html={html} />,
});
