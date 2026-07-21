import { cn } from "@/lib/utils";

/** A loading placeholder block. Screens compose these into skeleton layouts
 *  instead of spinners (see the design brief). */
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted/60", className)}
      {...props}
    />
  );
}

export default Skeleton;
