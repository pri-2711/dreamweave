import { createFileRoute } from "@tanstack/react-router";
import html from "@/screens/plan.html?raw";
import { Screen } from "@/components/Screen";

export const Route = createFileRoute("/plan")({
  head: () => ({
    meta: [
      { title: "Japan Trip Itinerary — DreamWeave" },
      { name: "description", content: "Day-by-day plan, bookings and budget for the Japan Trip." },
      { property: "og:title", content: "Japan Trip Itinerary — DreamWeave" },
      { property: "og:description", content: "Day-by-day plan, bookings and budget for the Japan Trip." },
    ],
  }),
  component: () => <Screen html={html} />,
});
