import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/vision.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/vision")({
  head: () => ({
    meta: [
      { title: "Japan Trip Vision Board — DreamWeave" },
      { name: "description", content: "A live moodboard canvas for the Japan Trip." },
      { property: "og:title", content: "Japan Trip Vision Board — DreamWeave" },
      { property: "og:description", content: "A live moodboard canvas for the Japan Trip." },
    ],
  }),
  component: () => <Screen html={html} />,
});
