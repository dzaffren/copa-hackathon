import { beforeEach, describe, expect, it } from "vitest";
import { fireEvent, screen } from "@testing-library/react";

import { DemoController } from "@/components/DemoController";
import { renderWithProviders } from "@/test/utils";

const POSITION_KEY = "wsb-demo-controller-position";
const STORAGE_KEY = "wsb-demo-controller-minimized";

/** jsdom gives every element a zero-size rect, which makes `clampToViewport`
 *  clamp any drag to (0,0) and hides a real move. Stub a realistic bar size so
 *  the clamp has room to work, mirroring the ~600x48 bar in the browser. */
function stubBarRect(el: HTMLElement) {
  el.getBoundingClientRect = () =>
    ({
      left: 0,
      top: 0,
      right: 600,
      bottom: 48,
      width: 600,
      height: 48,
      x: 0,
      y: 0,
      toJSON: () => {},
    }) as DOMRect;
}

function dragHandle() {
  return screen.getByLabelText("Drag to move demo walkthrough panel");
}

function bar() {
  return screen.getByRole("toolbar", { name: "Demo walkthrough" });
}

describe("DemoController drag", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem(STORAGE_KEY, "0");
  });

  it("moves the bar to the dragged position", () => {
    renderWithProviders(<DemoController />, "/");
    const handle = dragHandle();
    stubBarRect(bar());

    fireEvent.pointerDown(handle, {
      button: 0,
      pointerId: 1,
      clientX: 10,
      clientY: 10,
    });
    fireEvent.pointerMove(handle, { pointerId: 1, clientX: 210, clientY: 110 });
    fireEvent.pointerUp(handle, { pointerId: 1 });

    // Grabbed 10px into the bar, released at (210,110) → bar origin (200,100).
    expect(bar().style.left).toBe("200px");
    expect(bar().style.top).toBe("100px");
  });

  it("persists the dragged position to localStorage", () => {
    renderWithProviders(<DemoController />, "/");
    const handle = dragHandle();
    stubBarRect(bar());

    fireEvent.pointerDown(handle, {
      button: 0,
      pointerId: 1,
      clientX: 0,
      clientY: 0,
    });
    fireEvent.pointerMove(handle, { pointerId: 1, clientX: 150, clientY: 90 });
    fireEvent.pointerUp(handle, { pointerId: 1 });

    expect(
      JSON.parse(window.localStorage.getItem(POSITION_KEY) ?? "null"),
    ).toEqual({
      left: 150,
      top: 90,
    });
  });

  it("restores a stored position on mount", () => {
    window.localStorage.setItem(
      POSITION_KEY,
      JSON.stringify({ left: 42, top: 24 }),
    );
    renderWithProviders(<DemoController />, "/");

    expect(bar().style.left).toBe("42px");
    expect(bar().style.top).toBe("24px");
  });

  it("ignores a non-primary button press", () => {
    renderWithProviders(<DemoController />, "/");
    const handle = dragHandle();
    stubBarRect(bar());

    fireEvent.pointerDown(handle, {
      button: 2,
      pointerId: 1,
      clientX: 10,
      clientY: 10,
    });
    fireEvent.pointerMove(handle, { pointerId: 1, clientX: 210, clientY: 110 });

    expect(bar().style.left).toBe("");
  });

  it("keeps the handle clickable — the bar sets pointer-events-none", () => {
    // The bar container is `pointer-events-none` and re-enables only
    // `[&_button]` / `[&_select]` descendants. The drag handle is a
    // `div[role=button]`, NOT a <button>, so it must carry its own
    // `pointer-events-auto` or the drag can never start in a real browser.
    renderWithProviders(<DemoController />, "/");
    expect(dragHandle().className).toContain("pointer-events-auto");
  });
});
