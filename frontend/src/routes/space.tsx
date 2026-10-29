import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/space.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/space")({
  head: () => ({
    meta: [
      { title: "Japan Trip Overview — DreamWeave" },
      { name: "description", content: "Overview of the Japan Trip space: pins, destinations, budget and progress." },
      { property: "og:title", content: "Japan Trip Overview — DreamWeave" },
      { property: "og:description", content: "Overview of the Japan Trip space: pins, destinations, budget and progress." },
    ],
  }),
  component: () => <Screen html={html} />,
});
