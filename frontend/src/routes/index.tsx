import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/home.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DreamWeave — Your creative spaces" },
      { name: "description", content: "Collect ideas, trips and goals into beautiful spaces with DreamWeave." },
      { property: "og:title", content: "DreamWeave — Your creative spaces" },
      { property: "og:description", content: "Collect ideas, trips and goals into beautiful spaces with DreamWeave." },
    ],
  }),
  component: () => <Screen html={html} />,
});
