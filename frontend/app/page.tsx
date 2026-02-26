"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.backend))
      .catch(() => setStatus("Backend not reachable"));
  }, []);

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Fast Food Value Optimizer</h1>
      <p className="mt-4">Backend status: {status}</p>
    </main>
  );
}