import { useEffect, useRef } from "react";

export default function HomePage() {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!boxRef.current) return;

    const animation = boxRef.current.animate(
      [
        { transform: "translateX(0) rotate(0deg)" },
        { transform: "translateX(250px) rotate(360deg)" },
      ],
      { duration: 1000, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
    );

    return () => animation.cancel();
  }, []);

  return (
    <div
      ref={boxRef}
      style={{
        width: "100px",
        height: "100px",
        backgroundColor: "dodgerblue",
      }}
    />
  );
}