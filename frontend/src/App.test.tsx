import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp } from "@/test/utils";

describe("App smoke", () => {
  it("renders the home landing with a link into the task screen", () => {
    renderApp("/");
    const link = screen.getByRole("link", {
      name: /task screen/i,
    });
    expect(link).toHaveAttribute(
      "href",
      "/workstreams/opres-v2/tasks/opres-pd-v0-3",
    );
  });
});
