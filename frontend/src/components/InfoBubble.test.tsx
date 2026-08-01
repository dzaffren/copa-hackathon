import { describe, it, expect } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { InfoBubble } from "./InfoBubble";

describe("InfoBubble", () => {
  it("reveals its note on hover", async () => {
    const user = userEvent.setup();
    render(<InfoBubble>Not verifiable from these documents.</InfoBubble>);

    // Closed until asked for — the note is an aside about what the tool could
    // not verify, not part of the recommendation's reading flow.
    expect(screen.queryByTestId("info-bubble")).toBeNull();

    await user.hover(screen.getByRole("button"));

    expect(await screen.findByTestId("info-bubble")).toHaveTextContent(
      "Not verifiable from these documents.",
    );
  });

  it("reveals its note on keyboard focus, reached by Tab", async () => {
    const user = userEvent.setup();
    render(<InfoBubble>Assumes no industry register exists.</InfoBubble>);

    // A real <button>, so Tab lands on it — a hover-only marker would hide the
    // note from anyone not using a pointer.
    await user.tab();
    expect(screen.getByRole("button")).toHaveFocus();

    expect(await screen.findByTestId("info-bubble")).toHaveTextContent(
      "Assumes no industry register exists.",
    );
  });

  it("reveals its note on a tap, where there is no hover to give", async () => {
    render(<InfoBubble>Scope of the register is assumed.</InfoBubble>);

    // A bare click, not userEvent.click: userEvent moves a mouse pointer first,
    // which would open the bubble via onMouseEnter and prove nothing about the
    // touch path. A tap on a touchscreen delivers the click alone.
    fireEvent.click(screen.getByRole("button"));

    expect(await screen.findByTestId("info-bubble")).toHaveTextContent(
      "Scope of the register is assumed.",
    );
    // Tapping the marker again puts it away — a touchscreen has no Escape key.
    fireEvent.click(screen.getByRole("button"));
    expect(screen.queryByTestId("info-bubble")).toBeNull();
  });

  it("puts the note away on Escape, without moving focus off the marker", async () => {
    const user = userEvent.setup();
    render(<InfoBubble>Not verifiable from these documents.</InfoBubble>);

    await user.tab();
    expect(await screen.findByTestId("info-bubble")).toBeInTheDocument();

    await user.keyboard("{Escape}");

    // Dismissed, and the drafter keeps her place in the tab order — Escape is
    // "hide this", not "leave".
    await waitFor(() => expect(screen.queryByTestId("info-bubble")).toBeNull());
    expect(screen.getByRole("button")).toHaveFocus();
  });

  it("puts the note away when focus or the pointer leaves", async () => {
    const user = userEvent.setup();
    render(
      <>
        <InfoBubble>Not verifiable from these documents.</InfoBubble>
        <button type="button">Generate</button>
      </>,
    );

    // Tabbing on to the next control closes it — otherwise a bubble opened by
    // keyboard would follow the drafter down the page.
    await user.tab();
    expect(await screen.findByTestId("info-bubble")).toBeInTheDocument();
    await user.tab();
    await waitFor(() => expect(screen.queryByTestId("info-bubble")).toBeNull());

    // Same for the pointer: moving off the marker closes it.
    const marker = screen.getAllByRole("button")[0];
    await user.hover(marker);
    expect(await screen.findByTestId("info-bubble")).toBeInTheDocument();
    await user.unhover(marker);
    await waitFor(() => expect(screen.queryByTestId("info-bubble")).toBeNull());
  });

  it("names the marker for a screen reader, generically or per caller", async () => {
    const { unmount } = render(<InfoBubble>A note.</InfoBubble>);

    // The icon carries no text, so without a name the marker announces as an
    // unlabelled button.
    expect(
      screen.getByRole("button", { name: "More information" }),
    ).toBeInTheDocument();
    unmount();

    render(<InfoBubble label="What could not be verified">A note.</InfoBubble>);
    expect(
      screen.getByRole("button", { name: "What could not be verified" }),
    ).toBeInTheDocument();
  });

  it("points the marker at its own bubble, and only while open", async () => {
    const user = userEvent.setup();
    render(
      <>
        <InfoBubble label="First">First note.</InfoBubble>
        <InfoBubble label="Second">Second note.</InfoBubble>
      </>,
    );

    const first = screen.getByRole("button", { name: "First" });
    const second = screen.getByRole("button", { name: "Second" });

    // Closed: nothing to describe it with, and the marker says so.
    expect(first).not.toHaveAttribute("aria-describedby");
    expect(first).toHaveAttribute("aria-expanded", "false");

    await user.hover(first);
    const bubble = await screen.findByTestId("info-bubble");
    expect(first).toHaveAttribute("aria-describedby", bubble.id);
    expect(first).toHaveAttribute("aria-expanded", "true");
    // Two markers on one page must not describe the same element — every
    // recommendation on the card carries one.
    expect(bubble.id).toBeTruthy();
    expect(second).not.toHaveAttribute("aria-describedby");

    await user.hover(second);
    const secondBubble = await screen.findByTestId("info-bubble");
    expect(second).toHaveAttribute("aria-describedby", secondBubble.id);
    expect(secondBubble.id).not.toBe(bubble.id);
  });

  it("renders its note as text, never as markup", async () => {
    const user = userEvent.setup();
    // A confidence note comes back from a model, so it is untrusted input.
    render(
      <InfoBubble>
        {"Assumes <b>no</b> register <img src=x> exists."}
      </InfoBubble>,
    );

    await user.hover(screen.getByRole("button"));
    const bubble = await screen.findByTestId("info-bubble");

    // The angle brackets survive as characters; no element is created from them.
    expect(bubble).toHaveTextContent(
      "Assumes <b>no</b> register <img src=x> exists.",
    );
    expect(bubble.querySelector("b")).toBeNull();
    expect(bubble.querySelector("img")).toBeNull();
  });
});
