
import { useEffect, useRef, useState } from "react";
import { animate, createTimeline, stagger } from "animejs";

export default function PlaceholderPage() {
  
   const root = useRef<HTMLDivElement>(null);
   useEffect(() => {
    const el = root.current;
  
    if (!el) return;
  
    const tl = createTimeline({
      defaults: { ease: "outExpo" }
    })
      .add(el.querySelectorAll(".kpi-hero"), {
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800
      })
      .add(el.querySelectorAll(".kpi-card"), {
        opacity: [0, 1],
        translateY: [16, 0],
        duration: 700,
        delay: stagger(100)
      }, "-=500");
      const counters = Array.from(el.querySelectorAll<HTMLElement>("[data-count]")).flatMap((node) => {
        const target = Number(node.dataset.count);
        if (Number.isNaN(target)||!node.firstChild)return [];
        const obj ={v:0};
        return [
          animate(obj, {
            v: target,
            duration: 1400,
            delay: 300,
            ease: "outExpo",
            onUpdate: () => {
              node.firstChild!.nodeValue = Math.round(obj.v).toLocaleString();
            },
          }),
          ];
          }); // closes flatMap
          return () => {
            tl.revert();
            counters.forEach((counter) => counter.revert());
          };
      
        }, []);
          
        
   

      
        
  
       


  return (
    <div ref = {root} className="mx-auto max-w-6xl">
      <section className="kpi-hero mb-8 rounded-2xl bg-[#1E152A]  p-8 text-white">
        <h1 className = "text-3xl font-bold">
          Your Progress
        </h1>
        <p className="mt-2 text-slate-300 ">
          Here is how youe doing! 
          </p>
      </section>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

  <div className="kpi-card rounded-2xl bg-[#E1EAD5] p-6 shadow">
    <h2 className="text-sm text-slate-500">
      placeholder
    </h2>
    <p data-count="24" className="mt-2 text-3xl font-bold">
      0
    </p>
  </div>

  <div className="kpi-card rounded-2xl bg-[#E1EAD5] p-6 shadow">
    <h2 className="text-sm text-[A71D31]">
      placeholder
    </h2>
    <p data-count="8" className="mt-2 text-3xl font-bold">
      0
    </p>
  </div>

  <div className="kpi-card rounded-2xl bg-[#E1EAD5] p-6 shadow">
    <h2 className="text-sm text-slate-500">
      placeholder
    </h2>
    <p data-count="1250" className="mt-2 text-3xl font-bold text-[#222520]">
      0
    </p>
  </div>

</div>





    </div>
    );
  }
  
